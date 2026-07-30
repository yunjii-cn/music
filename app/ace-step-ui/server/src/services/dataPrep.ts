/**
 * One-click training data preparation service (训练数据一键准备).
 *
 * Node-side orchestration of the *existing* Python dataset endpoints:
 *   scan -> auto_label_async (transcribe lyrics + LLM caption/BPM/Key)
 *        -> save -> preprocess_async
 *
 * Mirrors the design of quickTrain.ts: an in-memory task state machine that
 * the front-end polls via `GET /api/training/data-prep-status/:id`.
 * No new Python endpoints are required.
 */

import path from 'path';
import { proxyToAceStep } from '../routes/training.js';

export type DataPrepStage =
  | 'pending'
  | 'scanning'
  | 'labeling'
  | 'saving'
  | 'preprocessing'
  | 'completed'
  | 'failed';

export interface DataPrepParams {
  folder: string;            // audio directory to scan
  name: string;              // dataset name
  tag?: string;              // custom activation tag
  tagPosition?: 'prepend' | 'append' | 'replace';
  hasVocals?: boolean;       // true => transcribe lyrics from audio
  skipMetas?: boolean;       // skip BPM/Key/TimeSig generation
  onlyUnlabeled?: boolean;   // only label unlabeled samples
  outputDir?: string;        // optional override for dataset/tensor output root
}

export interface DataPrepTask {
  id: string;
  stage: DataPrepStage;
  progress: number; // 0-100
  message: string;
  status: 'running' | 'completed' | 'failed';
  dataset_json?: string;
  tensor_dir?: string;
  sample_count?: number;
  error?: string;
  cancelled?: boolean;
  created_at: number;
  updated_at: number;
}

const tasks = new Map<string, DataPrepTask>();

export function getDataPrepTask(id: string): DataPrepTask | undefined {
  return tasks.get(id);
}

export function cancelDataPrep(id: string): DataPrepTask | undefined {
  const task = tasks.get(id);
  if (!task) return undefined;
  if (task.status === 'completed') return task;
  task.cancelled = true;
  task.stage = 'failed';
  task.status = 'failed';
  task.message = '已取消';
  task.error = 'cancelled';
  task.updated_at = Date.now();
  return task;
}

function update(task: DataPrepTask, stage: DataPrepStage, progress: number, message: string) {
  if (task.cancelled) return;
  task.stage = stage;
  task.progress = Math.max(0, Math.min(100, Math.round(progress)));
  task.message = message;
  task.updated_at = Date.now();
}

function assertAlive(task: DataPrepTask) {
  if (task.cancelled) throw new Error('cancelled');
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

function sanitizeName(name: string): string {
  const cleaned = (name || 'my_dataset').trim().replace(/[^\w\-]+/g, '_').replace(/^_+|_+$/g, '');
  return cleaned || 'my_dataset';
}

export function startDataPrep(params: DataPrepParams): DataPrepTask {
  const id = crypto.randomUUID();
  const task: DataPrepTask = {
    id,
    stage: 'pending',
    progress: 0,
    message: '已加入队列',
    status: 'running',
    created_at: Date.now(),
    updated_at: Date.now(),
  };
  tasks.set(id, task);
  runDataPrep(id, params).catch((err: any) => {
    task.stage = 'failed';
    task.status = 'failed';
    task.error = err?.message || String(err);
    task.message = task.error === 'cancelled' ? '已取消' : `失败: ${task.error}`;
    task.updated_at = Date.now();
  });
  return task;
}

async function runDataPrep(id: string, params: DataPrepParams): Promise<void> {
  const task = tasks.get(id)!;
  const hasVocals = params.hasVocals !== false; // default: transcribe

  // --- 0. Resolve output root ------------------------------------------------
  update(task, 'scanning', 2, '读取环境信息...');
  const profile = (await proxyToAceStep('/v1/training/env-profile', 'GET')) as any;
  const outputsRoot: string = params.outputDir || profile?.lora_outputs_root;
  if (!outputsRoot) throw new Error('无法获取输出根目录 (lora_outputs_root)');

  const name = sanitizeName(params.name);
  const baseDir = path.join(outputsRoot, name);
  const tensorsDir = path.join(baseDir, 'tensors');
  const datasetJson = path.join(baseDir, 'dataset.json');
  const tag = (params.tag || '').trim();
  const tagPosition = params.tagPosition || 'append';

  // --- 1. Scan ----------------------------------------------------------------
  assertAlive(task);
  update(task, 'scanning', 5, '扫描音频文件夹...');
  const scan = (await proxyToAceStep('/v1/dataset/scan', 'POST', {
    audio_dir: params.folder,
    dataset_name: name,
    custom_tag: tag,
    tag_position: tagPosition,
    all_instrumental: !hasVocals,
  })) as any;
  const samples: any[] = scan?.samples || [];
  if (!samples.length) throw new Error('文件夹中没有找到音频文件（支持 wav/mp3/flac/ogg/opus）');
  task.sample_count = samples.length;
  update(task, 'scanning', 10, `找到 ${samples.length} 个音频文件`);

  // --- 2. Auto label (transcribe + LLM caption/BPM/Key), async + poll ---------
  assertAlive(task);
  update(task, 'labeling', 12, hasVocals ? '自动打标（含歌词转写）...' : '自动打标...');
  const label = (await proxyToAceStep('/v1/dataset/auto_label_async', 'POST', {
    skip_metas: !!params.skipMetas,
    format_lyrics: false,
    transcribe_lyrics: hasVocals,
    only_unlabeled: !!params.onlyUnlabeled,
    save_path: datasetJson, // persist progress during labeling
  })) as any;
  const labelTaskId: string = label?.task_id;
  if (labelTaskId) {
    // Labeling (transcriber + LLM) is the slow part: 12% -> 70%
    for (let attempt = 0; attempt < 14400; attempt++) { // up to ~8h @2s
      assertAlive(task);
      const st = (await proxyToAceStep(`/v1/dataset/auto_label_status/${labelTaskId}`, 'GET')) as any;
      if (st?.status === 'completed') break;
      if (st?.status === 'failed') throw new Error(st?.error || '自动打标失败');
      const cur = Number(st?.current || 0);
      const tot = Number(st?.total || samples.length || 1);
      const pct = tot > 0 ? cur / tot : 0;
      update(task, 'labeling', 12 + Math.round(pct * 58), st?.progress || `打标中 ${cur}/${tot}...`);
      await sleep(2000);
    }
  }

  // --- 3. Save dataset ----------------------------------------------------------
  assertAlive(task);
  update(task, 'saving', 72, '保存数据集...');
  await proxyToAceStep('/v1/dataset/save', 'POST', {
    save_path: datasetJson,
    dataset_name: name,
    custom_tag: tag,
    tag_position: tagPosition,
    all_instrumental: !hasVocals,
  });

  // --- 4. Preprocess tensors (async + poll) --------------------------------------
  assertAlive(task);
  update(task, 'preprocessing', 75, '预处理张量...');
  const prep = (await proxyToAceStep('/v1/dataset/preprocess_async', 'POST', {
    output_dir: tensorsDir,
  })) as any;
  const prepId: string = prep?.task_id;
  if (prepId) {
    for (let attempt = 0; attempt < 7200; attempt++) { // up to ~4h @2s
      assertAlive(task);
      const st = (await proxyToAceStep(`/v1/dataset/preprocess_status/${prepId}`, 'GET')) as any;
      if (st?.status === 'completed') break;
      if (st?.status === 'failed') throw new Error(st?.error || '预处理失败');
      const cur = Number(st?.current || 0);
      const tot = Number(st?.total || 1);
      const pct = tot > 0 ? cur / tot : 0;
      update(task, 'preprocessing', 75 + Math.round(pct * 24), st?.progress || '预处理中...');
      await sleep(2000);
    }
  }

  // --- Done -----------------------------------------------------------------------
  task.dataset_json = datasetJson;
  task.tensor_dir = tensorsDir;
  update(task, 'completed', 100, `数据准备完成：${samples.length} 个样本，张量已就绪，可直接开始训练`);
  task.status = 'completed';
}
