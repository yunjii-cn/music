import React, { useState, useEffect, useRef } from 'react';
import { Zap, FolderOpen, Play, Square, ChevronDown, ChevronUp, Cpu, CheckCircle2, XCircle } from 'lucide-react';
import { useI18n } from '../context/I18nContext';
import { useAuth } from '../context/AuthContext';
import { trainingApi } from '../services/api';
import { TrainingAdvancedParams, TrainingParams } from './TrainingAdvancedParams';
import { CAPTION_TEMPLATE, previewCaption } from '../data/qualityPresets';

interface Props {
  trainingParams: TrainingParams;
  onTrainingParamsChange: (patch: Partial<TrainingParams>) => void;
  modelVariant: string;
  onModelVariantChange: (v: string) => void;
}

type Stage =
  | 'pending' | 'scanning' | 'labeling' | 'saving'
  | 'preprocessing' | 'training' | 'exporting' | 'registered' | 'failed';

const STAGE_KEY: Record<Stage, string> = {
  pending: 'quickStageScanning',
  scanning: 'quickStageScanning',
  labeling: 'quickStageLabeling',
  saving: 'quickStageSaving',
  preprocessing: 'quickStagePreprocessing',
  training: 'quickStageTraining',
  exporting: 'quickStageExporting',
  registered: 'quickStageRegistered',
  failed: 'quickStageFailed',
};

const TIER_KEY: Record<string, string> = {
  full: 'quickTierFull',
  fp8: 'quickTierFp8',
  low: 'quickTierLow',
  unknown: 'quickTierUnknown',
};

export const QuickTrainPanel: React.FC<Props> = ({ trainingParams, onTrainingParamsChange, modelVariant, onModelVariantChange }) => {
  const { t } = useI18n();
  const { token } = useAuth();

  const [folder, setFolder] = useState('');
  const [name, setName] = useState('');
  const [tag, setTag] = useState('');
  const [quality, setQuality] = useState<'fast' | 'balanced' | 'quality'>('balanced');
  const [captionTemplate, setCaptionTemplate] = useState(CAPTION_TEMPLATE);
  const [advancedOpen, setAdvancedOpen] = useState(false);

  const [env, setEnv] = useState<any>(null);
  const [envError, setEnvError] = useState('');

  const [taskId, setTaskId] = useState<string | null>(null);
  const [task, setTask] = useState<any>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Load environment profile on mount.
  useEffect(() => {
    if (!token) return;
    trainingApi.getEnvProfile(token)
      .then(setEnv)
      .catch((e) => setEnvError(e?.message || 'env profile failed'));
  }, [token]);

  // Poll quick-train status.
  useEffect(() => {
    if (!taskId || !token) return;
    pollRef.current = setInterval(async () => {
      try {
        const st = await trainingApi.getQuickStatus(taskId, token);
        setTask(st);
        if (st.status === 'completed' || st.status === 'failed') {
          if (pollRef.current) clearInterval(pollRef.current);
        }
      } catch {
        if (pollRef.current) clearInterval(pollRef.current);
      }
    }, 2000);
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [taskId, token]);

  const start = async () => {
    if (!token) return;
    if (!folder.trim() || !name.trim()) return;
    try {
      const res = await trainingApi.quickTrain({
        folder: folder.trim(),
        name: name.trim(),
        tag: tag.trim(),
        quality,
        captionTemplate,
        advanced: trainingParams,
      }, token);
      setTaskId(res.id);
      setTask(res);
    } catch (e: any) {
      setTask({ status: 'failed', error: e?.message, stage: 'failed', progress: 0, message: e?.message });
    }
  };

  const cancel = async () => {
    if (!taskId || !token) return;
    try {
      await trainingApi.cancelQuickTrain(taskId, token);
    } catch { /* ignore */ }
  };

  const isRunning = task?.status === 'running';
  const captionPreview = previewCaption(quality, tag, captionTemplate);

  return (
    <div className="space-y-6">
      {/* Environment profile banner */}
      <div className="bg-gradient-to-br from-cyan-50 to-blue-50 dark:from-cyan-950/30 dark:to-blue-950/30 rounded-xl p-4 border-2 border-cyan-200 dark:border-cyan-800 shadow-md">
        <div className="flex items-center gap-2 mb-2">
          <Cpu className="text-cyan-600 dark:text-cyan-400" size={18} />
          <h3 className="text-base font-semibold text-zinc-900 dark:text-white">{t('quickEnv')}</h3>
        </div>
        {envError && <div className="text-sm text-red-500">{envError}</div>}
        {env ? (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
            <div className="bg-white/60 dark:bg-zinc-900/40 rounded-lg p-3">
              <div className="text-zinc-500 dark:text-zinc-400">{t('quickVram')}</div>
              <div className="font-semibold text-zinc-900 dark:text-white">
                {env.vram_total_mb ? `${(env.vram_total_mb / 1024).toFixed(1)} GB` : 'N/A'}
                <span className="ml-2 text-xs px-2 py-0.5 rounded-full bg-zinc-200 dark:bg-zinc-700">
                  {t(TIER_KEY[env.tier] || 'quickTierUnknown')}
                </span>
              </div>
            </div>
            <div className="bg-white/60 dark:bg-zinc-900/40 rounded-lg p-3">
              <div className="text-zinc-500 dark:text-zinc-400">{t('quickRecommendedVariant')}</div>
              <div className="font-semibold text-zinc-900 dark:text-white">
                {env.recommended_variant ? env.recommended_variant : t('quickNoVariant')}
              </div>
            </div>
            <div className="bg-white/60 dark:bg-zinc-900/40 rounded-lg p-3">
              <div className="text-zinc-500 dark:text-zinc-400">{t('quickDownloadedVariants')}</div>
              <div className="font-semibold text-zinc-900 dark:text-white">
                {(env.downloaded_variants && env.downloaded_variants.length) ? env.downloaded_variants.join(', ') : t('none')}
              </div>
            </div>
          </div>
        ) : !envError ? (
          <div className="text-sm text-zinc-500">{t('loading')}</div>
        ) : null}
        {env && env.tier === 'low' && (
          <div className="mt-3 text-sm text-amber-600 dark:text-amber-400">
            ⚠️ {t('quickLowVramHint')}
          </div>
        )}
      </div>

      {/* Basic inputs */}
      <div className="bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-950/30 dark:to-pink-950/30 rounded-xl p-4 space-y-4 border-2 border-purple-200 dark:border-purple-800 shadow-md">
        <h3 className="text-base font-semibold text-zinc-900 dark:text-white">🎵 {t('quickBasic')}</h3>

        <div>
          <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">{t('audioFolder')}</label>
          <div className="flex gap-2">
            <input type="text" value={folder} onChange={(e) => setFolder(e.target.value)}
              placeholder="/path/to/your/audio/folder"
              className="flex-1 px-3 py-2 bg-white dark:bg-zinc-900 border border-zinc-300 dark:border-zinc-700 rounded-lg text-sm text-zinc-900 dark:text-white placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-pink-500" />
            <span className="px-3 py-2 bg-zinc-100 dark:bg-zinc-800 rounded-lg text-xs text-zinc-500 flex items-center">
              <FolderOpen size={14} className="mr-1" />{t('audioFolderHint')}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">{t('loraName')}</label>
            <input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="my_style_lora"
              className="w-full px-3 py-2 bg-white dark:bg-zinc-900 border border-zinc-300 dark:border-zinc-700 rounded-lg text-sm text-zinc-900 dark:text-white placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-pink-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">{t('styleTag')}</label>
            <input type="text" value={tag} onChange={(e) => setTag(e.target.value)} placeholder="lofi, jazz..."
              className="w-full px-3 py-2 bg-white dark:bg-zinc-900 border border-zinc-300 dark:border-zinc-700 rounded-lg text-sm text-zinc-900 dark:text-white placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-pink-500" />
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">{t('quality')}</label>
            <div className="flex gap-2">
              {(['fast', 'balanced', 'quality'] as const).map((q) => (
                <button key={q} onClick={() => setQuality(q)}
                  className={`flex-1 py-2.5 rounded-lg text-sm font-medium border-2 transition-all ${
                    quality === q
                      ? 'border-pink-500 bg-pink-500 text-white'
                      : 'border-zinc-300 dark:border-zinc-700 text-zinc-600 dark:text-zinc-300 hover:border-pink-300'
                  }`}>
                  {t(`quality${q.charAt(0).toUpperCase() + q.slice(1)}` as any)}
                  <span className="block text-[10px] font-normal opacity-80">
                    {t(`quality${q.charAt(0).toUpperCase() + q.slice(1)}Desc` as any)}
                  </span>
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">{t('modelVariant')}</label>
            <div className="flex gap-2">
              {['turbo', 'sft', 'base'].map((v) => (
                <button key={v} onClick={() => onModelVariantChange(v)}
                  className={`flex-1 py-2.5 rounded-lg text-sm font-medium border-2 transition-all ${
                    modelVariant === v
                      ? 'border-indigo-500 bg-indigo-500 text-white'
                      : 'border-zinc-300 dark:border-zinc-700 text-zinc-600 dark:text-zinc-300 hover:border-indigo-300'
                  }`}>
                  {v.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">{t('captionTemplate')}</label>
          <input type="text" value={captionTemplate} onChange={(e) => setCaptionTemplate(e.target.value)} placeholder={CAPTION_TEMPLATE}
            className="w-full px-3 py-2 bg-white dark:bg-zinc-900 border border-zinc-300 dark:border-zinc-700 rounded-lg text-sm text-zinc-900 dark:text-white placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-pink-500" />
          <div className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
            {t('captionPreview')}: <span className="text-pink-500 font-medium">{captionPreview}</span>
          </div>
        </div>
      </div>

      {/* Advanced collapsible (shares state with the 训练 tab) */}
      <div className="rounded-xl border-2 border-zinc-200 dark:border-zinc-700 overflow-hidden">
        <button onClick={() => setAdvancedOpen(!advancedOpen)}
          className="w-full flex items-center justify-between px-4 py-3 bg-zinc-100 dark:bg-zinc-800 text-sm font-semibold text-zinc-900 dark:text-white">
          <span>🔧 {t('advanced')}</span>
          {advancedOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </button>
        {advancedOpen && (
          <div className="p-4 bg-white dark:bg-zinc-900 space-y-4">
            <TrainingAdvancedParams value={trainingParams} onChange={onTrainingParamsChange} hideOutputDir />
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex gap-4">
        <button onClick={start} disabled={isRunning || !folder.trim() || !name.trim()}
          className={`flex-1 py-3 rounded-lg font-medium flex items-center justify-center gap-2 transition-all ${
            isRunning || !folder.trim() || !name.trim()
              ? 'bg-zinc-300 dark:bg-zinc-700 text-zinc-500 cursor-not-allowed'
              : 'bg-gradient-to-r from-pink-500 to-rose-500 hover:from-pink-600 hover:to-rose-600 text-white'
          }`}>
          <Zap size={18} />{t('startQuickTrain')}
        </button>
        {isRunning && (
          <button onClick={cancel}
            className="flex-1 py-3 rounded-lg font-medium flex items-center justify-center gap-2 bg-gradient-to-r from-red-500 to-pink-500 hover:from-red-600 hover:to-pink-600 text-white transition-all">
            <Square size={18} />{t('quickCancel')}
          </button>
        )}
      </div>

      {/* Progress */}
      {task && (
        <div className={`rounded-xl p-5 border-2 shadow-lg space-y-3 ${
          task.status === 'failed'
            ? 'bg-red-50 dark:bg-red-950/30 border-red-300 dark:border-red-800'
            : task.status === 'completed'
              ? 'bg-emerald-50 dark:bg-emerald-950/30 border-emerald-300 dark:border-emerald-800'
              : 'bg-gradient-to-br from-indigo-50 to-violet-50 dark:from-indigo-950/30 dark:to-violet-950/30 border-indigo-200 dark:border-indigo-800'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-semibold text-zinc-900 dark:text-white">
              {task.status === 'completed' ? <CheckCircle2 size={18} className="text-emerald-500" />
                : task.status === 'failed' ? <XCircle size={18} className="text-red-500" />
                : <Play size={18} className="text-indigo-500" />}
              {t(STAGE_KEY[(task.stage as Stage) || 'pending'] || 'quickStageScanning')}
            </div>
            <span className="text-sm text-zinc-500">{task.progress ?? 0}%</span>
          </div>
          <div className="w-full h-2 bg-zinc-200 dark:bg-zinc-700 rounded-full overflow-hidden">
            <div className="h-full bg-gradient-to-r from-pink-500 to-rose-500 transition-all"
              style={{ width: `${task.progress ?? 0}%` }} />
          </div>
          {task.message && (
            <div className="text-xs text-zinc-600 dark:text-zinc-300 whitespace-pre-wrap break-words">
              {task.message}
            </div>
          )}
          {task.error && (
            <div className="text-xs text-red-500 break-words">{task.error}</div>
          )}
          {task.status === 'completed' && task.lora_path && (
            <div className="text-xs text-emerald-600 dark:text-emerald-400">
              📍 {task.lora_path}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
