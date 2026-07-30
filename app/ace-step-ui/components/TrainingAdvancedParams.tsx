import React from 'react';
import { useI18n } from '../context/I18nContext';

/** Shape of the shared advanced training parameters. */
export interface TrainingParams {
  loraRank: number;
  loraAlpha: number;
  loraDropout: number;
  learningRate: number;
  trainEpochs: number;
  trainBatchSize: number;
  gradientAccumulation: number;
  saveEveryNEpochs: number;
  trainingShift: number;
  trainingSeed: number;
  loraOutputDir: string;
  useFP8: boolean;
  gradientCheckpointing: boolean;
}

export const DEFAULT_TRAINING_PARAMS: TrainingParams = {
  loraRank: 64,
  loraAlpha: 128,
  loraDropout: 0.1,
  learningRate: 3e-4,
  trainEpochs: 1000,
  trainBatchSize: 1,
  gradientAccumulation: 1,
  saveEveryNEpochs: 200,
  trainingShift: 3.0,
  trainingSeed: 42,
  loraOutputDir: './lora_output',
  useFP8: false,
  gradientCheckpointing: false,
};

interface Props {
  value: TrainingParams;
  onChange: (patch: Partial<TrainingParams>) => void;
  /** Hide the LoRA output directory field (one-click training manages it). */
  hideOutputDir?: boolean;
}

/**
 * Reusable advanced training-parameter form.
 *
 * It is rendered BOTH inside the "训练" tab and the "一键训练" tab so the two
 * share a single source of truth (the parent's ``trainingParams`` state).
 */
export const TrainingAdvancedParams: React.FC<Props> = ({ value, onChange, hideOutputDir }) => {
  const { t } = useI18n();
  const set = (k: keyof TrainingParams, v: any) => onChange({ [k]: v } as Partial<TrainingParams>);

  return (
    <>
      {/* LoRA Settings */}
      <div className="bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-950/30 dark:to-pink-950/30 rounded-xl p-4 space-y-4 border-2 border-purple-200 dark:border-purple-800 shadow-md">
        <h3 className="text-base font-semibold text-zinc-900 dark:text-white">⚙️ {t('loraSettings')}</h3>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
              {t('loraRank')}: {value.loraRank}
            </label>
            <input type="range" min="4" max="256" step="4" value={value.loraRank}
              onChange={(e) => set('loraRank', Number(e.target.value))} className="w-full" />
          </div>
          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
              {t('loraAlpha')}: {value.loraAlpha}
            </label>
            <input type="range" min="4" max="512" step="4" value={value.loraAlpha}
              onChange={(e) => set('loraAlpha', Number(e.target.value))} className="w-full" />
          </div>
          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
              {t('dropout')}: {value.loraDropout.toFixed(2)}
            </label>
            <input type="range" min="0" max="0.5" step="0.05" value={value.loraDropout}
              onChange={(e) => set('loraDropout', Number(e.target.value))} className="w-full" />
          </div>
        </div>
      </div>

      {/* Training Parameters */}
      <div className="bg-gradient-to-br from-orange-50 to-amber-50 dark:from-orange-950/30 dark:to-amber-950/30 rounded-xl p-4 space-y-4 border-2 border-orange-200 dark:border-orange-800 shadow-md">
        <h3 className="text-base font-semibold text-zinc-900 dark:text-white">🎛️ {t('trainingParameters')}</h3>
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">{t('learningRate')}</label>
            <input type="number" value={value.learningRate} step="0.0001"
              onChange={(e) => set('learningRate', Number(e.target.value))}
              className="w-full px-3 py-2 bg-white dark:bg-zinc-900 border border-zinc-300 dark:border-zinc-700 rounded-lg text-sm text-zinc-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-pink-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">{t('maxEpochs')}: {value.trainEpochs}</label>
            <input type="range" min="100" max="4000" step="100" value={value.trainEpochs}
              onChange={(e) => set('trainEpochs', Number(e.target.value))} className="w-full" />
          </div>
          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">{t('batchSize')}: {value.trainBatchSize}</label>
            <input type="range" min="1" max="8" step="1" value={value.trainBatchSize}
              onChange={(e) => set('trainBatchSize', Number(e.target.value))} className="w-full" />
          </div>
          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">{t('gradientAccumulation')}: {value.gradientAccumulation}</label>
            <input type="range" min="1" max="16" step="1" value={value.gradientAccumulation}
              onChange={(e) => set('gradientAccumulation', Number(e.target.value))} className="w-full" />
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">{t('saveEvery')}: {value.saveEveryNEpochs} {t('epochs')}</label>
            <input type="range" min="50" max="1000" step="50" value={value.saveEveryNEpochs}
              onChange={(e) => set('saveEveryNEpochs', Number(e.target.value))} className="w-full" />
          </div>
          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">{t('shift')}: {value.trainingShift.toFixed(1)}</label>
            <input type="range" min="1" max="5" step="0.5" value={value.trainingShift}
              onChange={(e) => set('trainingShift', Number(e.target.value))} className="w-full" />
          </div>
          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">{t('seed')}</label>
            <input type="number" value={value.trainingSeed}
              onChange={(e) => set('trainingSeed', Number(e.target.value))}
              className="w-full px-3 py-2 bg-white dark:bg-zinc-900 border border-zinc-300 dark:border-zinc-700 rounded-lg text-sm text-zinc-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-pink-500" />
          </div>
        </div>

        {!hideOutputDir && (
          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">{t('outputDirectory')}</label>
            <input type="text" value={value.loraOutputDir}
              onChange={(e) => set('loraOutputDir', e.target.value)}
              className="w-full px-3 py-2 bg-white dark:bg-zinc-900 border border-zinc-300 dark:border-zinc-700 rounded-lg text-sm text-zinc-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-pink-500" />
          </div>
        )}

        <div className="flex items-center gap-3 p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
          <input type="checkbox" id="useFP8" checked={value.useFP8}
            onChange={(e) => set('useFP8', e.target.checked)}
            className="w-4 h-4 text-purple-600 bg-white dark:bg-zinc-800 border-zinc-300 dark:border-zinc-600 rounded focus:ring-purple-500" />
          <label htmlFor="useFP8" className="text-sm font-medium text-zinc-700 dark:text-zinc-300 cursor-pointer">
            ⚡ {t('useFP8')} <span className="text-xs text-zinc-500 dark:text-zinc-400">({t('fp8Description')})</span>
          </label>
        </div>

        <div className="flex items-center gap-3 p-3 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg border border-emerald-200 dark:border-emerald-800">
          <input type="checkbox" id="gradCheckpoint" checked={value.gradientCheckpointing}
            onChange={(e) => set('gradientCheckpointing', e.target.checked)}
            className="w-4 h-4 text-emerald-600 bg-white dark:bg-zinc-800 border-zinc-300 dark:border-zinc-600 rounded focus:ring-emerald-500" />
          <label htmlFor="gradCheckpoint" className="text-sm font-medium text-zinc-700 dark:text-zinc-300 cursor-pointer">
            🧊 {t('gradientCheckpointing')}
          </label>
        </div>
      </div>
    </>
  );
};
