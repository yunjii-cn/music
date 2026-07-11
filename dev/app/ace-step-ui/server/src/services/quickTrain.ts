/**
 * One-click training orchestration service (一键训练).
 *
 * Runs entirely on the Node side: it sequences the *existing* Python endpoints
 * (scan -> caption injection -> save -> preprocess-async -> training/start ->
 * export) and keeps an in-memory task state machine that the front-end polls
 * via `GET /api/training/quick-status/:id`.
 *
 * No new Python endpoints are invented for the pipeline itself; only
 * `/v1/training/env-profile` (used to locate the output root and pick a base
 * model) and the export step (which stamps `base_model`) are touched.
 */

import path from 'path';
import { proxyToAceStep } from '../routes/training.js';
import { CAPTION_TEMPLATE, resolveTrainingParams } from '../data/qualityPresets.js';

export type QuickStage =
  | 'pending'
  | 'scanning'
  | 'labeling'
  | 'saving'
  | 'preprocessing'
  | 'training'
  | 'exporting'
  | 'registered'
  | 'failed';

export interface QuickTrainParams {
  folder: string;
  name: string;
  tag: string;
  quality: 'fast' | 'balanced' | 'quality';
  captionTemplate?: string;
  advanced?: Record<string, any> | null;
}

export interface QuickTask {
  id: string;
  stage: QuickStage;
  progress: number; // 0-100
  message: string;
  status: 'running' | 'completed' | 'failed';
  lora_path?: string;
  error?: string;
  created_at: number;
  updated_at: number;
}

const tasks = new Map<string, QuickTask>();

export function getQuickTask(id: string): QuickTask | undefined {
  return tasks.get(id);
}

export function cancelQuickTrain(id: string): QuickTask | undefined {
  const task = tasks.get(id);
  if (!task) return undefined;
  if (task.status === 'completed') return task;
  // Ask the Python side to stop any in-flight training.
  proxyToAceStep('/v1/training/stop', 'POST').catch(() => {});
  task.stage = 'failed';
  task.status = 'failed';
  task.message = '已取消';
  task.error = 'cancelled';
  task.updated_at = Date.now();
  return task;
}

function update(task: QuickTask, stage: QuickStage, progress: number, message: string) {
  task.stage = stage;
  task.progress = Math.max(0, Math.min(100, Math.round(progress)));
  task.message = message;
  task.updated_at = Date.now();
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

function sanitizeName(name: string): string {
  const cleaned = (name || 'my_lora').trim().replace(/[^\w\-]+/g, '_').replace(/^_+|_+$/g, '');
  return cleaned || 'my_lora';
}

export function startQuickTrain(params: QuickTrainParams): QuickTask {
  const id = crypto.randomUUID();
  const task: QuickTask = {
    id,
    stage: 'pending',
    progress: 0,
    message: '已加入队列',
    status: 'running',
    created_at: Date.now(),
    updated_at: Date.now(),
  };
  tasks.set(id, task);
  // Fire-and-forget; the route returns immediately with the task id.
  runQuickTrain(id, params).catch((err: any) => {
    task.stage = 'failed';
    task.status = 'failed';
    task.error = err?.message || String(err);
    task.message = `失败: ${task.error}`;
    task.updated_at = Date.now();
  });
  return task;
}

async function runQuickTrain(id: string, params: QuickTrainParams): Promise<void> {
  const task = tasks.get(id)!;

  // --- 0. Environment profile (output root + recommended variant) ----------
  update(task, 'scanning', 2, '读取环境信息...');
  const profile = (await proxyToAceStep('/v1/training/env-profile', 'GET')) as any;
  const outputsRoot: string = profile?.lora_outputs_root;
  const projectRoot: string = profile?.project_root;
  const tier: string = profile?.tier || 'full';
  if (!outputsRoot) throw new Error('无法获取输出根目录 (lora_outputs_root)');

  const name = sanitizeName(params.name);
  const baseDir = path.join(outputsRoot, name);
  const tensorsDir = path.join(baseDir, 'tensors');
  const finalDir = path.join(baseDir, 'final');
  const datasetJson = path.join(baseDir, 'dataset.json');

  const variant: string = params.advanced?.variant || profile?.recommended_variant || 'turbo';
  const tag = (params.tag || '').trim();
  const template = params.captionTemplate || CAPTION_TEMPLATE;
  const caption = template.replace(/\{tag\}/g, tag || 'style');

  // --- 1. Scan --------------------------------------------------------------
  update(task, 'scanning', 8, '扫描音频文件夹...');
  const scan = (await proxyToAceStep('/v1/dataset/scan', 'POST', {
    audio_dir: params.folder,
    dataset_name: name,
    custom_tag: tag,
    tag_position: 'replace',
    all_instrumental: true,
  })) as any;
  const samples: any[] = scan?.samples || [];
  if (!samples.length) throw new Error('文件夹中没有找到音频文件');

  // --- 2. Label: inject the caption template into every sample -------------
  update(task, 'labeling', 18, `生成描述 (${samples.length} 个样本)...`);
  for (let i = 0; i < samples.length; i++) {
    await proxyToAceStep(`/v1/dataset/sample/${i}`, 'PUT', {
      caption,
      is_instrumental: true,
      lyrics: '[Instrumental]',
      labeled: true,
    });
    if (i % 5 === 0) {
      update(task, 'labeling', 18 + Math.round(((i + 1) / samples.length) * 12), `生成描述 ${i + 1}/${samples.length}...`);
    }
  }

  // --- 3. Save dataset ------------------------------------------------------
  update(task, 'saving', 35, '保存数据集...');
  await proxyToAceStep('/v1/dataset/save', 'POST', {
    save_path: datasetJson,
    dataset_name: name,
    custom_tag: tag,
    tag_position: 'replace',
    all_instrumental: true,
  });

  // --- 4. Preprocess (async + poll) ----------------------------------------
  update(task, 'preprocessing', 45, '预处理张量...');
  const prep = (await proxyToAceStep('/v1/dataset/preprocess_async', 'POST', {
    output_dir: tensorsDir,
  })) as any;
  const prepId: string = prep?.task_id;
  if (prepId) {
    for (let attempt = 0; attempt < 2000; attempt++) {
      const st = (await proxyToAceStep(`/v1/dataset/preprocess_status/${prepId}`, 'GET')) as any;
      if (st?.status === 'completed') break;
      if (st?.status === 'failed') throw new Error(st?.error || '预处理失败');
      const cur = Number(st?.current || 0);
      const tot = Number(st?.total || 1);
      const pct = tot > 0 ? Math.round((cur / tot) * 100) : 0;
      update(task, 'preprocessing', 45 + Math.round(pct * 0.2), st?.progress || '预处理中...');
      await sleep(1500);
    }
  }

  // --- 5. Training (start + poll) ------------------------------------------
  update(task, 'training', 70, '开始训练...');
  const tp = resolveTrainingParams(params.quality, params.advanced, variant, tier);
  await proxyToAceStep('/v1/training/start', 'POST', {
    tensor_dir: tensorsDir,
    lora_output_dir: baseDir,
    lora_rank: tp.lora_rank,
    lora_alpha: tp.lora_alpha,
    lora_dropout: tp.lora_dropout,
    learning_rate: tp.learning_rate,
    train_epochs: tp.train_epochs,
    train_batch_size: tp.train_batch_size,
    gradient_accumulation: tp.gradient_accumulation,
    save_every_n_epochs: tp.save_every_n_epochs,
    training_shift: tp.training_shift,
    training_seed: tp.training_seed,
    use_fp8: tp.use_fp8,
    gradient_checkpointing: tp.gradient_checkpointing,
  });

  let sawTraining = false;
  for (let attempt = 0; attempt < 1200; attempt++) {
    const st = (await proxyToAceStep('/v1/training/status', 'GET')) as any;
    if (st?.error) throw new Error(st.error);
    if (st?.is_training) sawTraining = true;
    if (sawTraining && !st?.is_training) break;
    const totalEp = Number(st?.config?.epochs || 1);
    const ep = Number(st?.current_epoch || 0);
    const pct = totalEp > 0 ? Math.round((ep / totalEp) * 100) : 0;
    update(task, 'training', 70 + Math.round(pct * 0.25), st?.status || '训练中...');
    await sleep(3000);
  }

  // --- 6. Export (stamps base_model into adapter_config.json) --------------
  update(task, 'exporting', 97, '导出 LoRA...');
  await proxyToAceStep('/v1/training/export', 'POST', {
    export_path: finalDir,
    lora_output_dir: baseDir,
    base_model: variant,
    model_variant: variant,
    model_variant_dir: '',
  });

  // Relative path (matching the discover endpoint's format) for the caller.
  const relPath = projectRoot
    ? path.relative(projectRoot, finalDir).split(path.sep).join('/')
    : finalDir;

  update(task, 'registered', 100, 'LoRA 训练完成，已加入「我的 LoRA」');
  task.lora_path = relPath;
  task.status = 'completed';
}
