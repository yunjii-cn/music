/**
 * Front-end quality presets for the "one-click training" (一键训练) feature.
 *
 * This file MIRRORS `acestep/training_v2/quick_presets.py` (the Python single
 * source of truth).  Keep the numeric values in sync with that module.
 *
 * It is used both for UI preview text and for computing the actual training
 * hyper-parameters on the Node orchestration side (`quickTrain.ts`).
 */

export type QualityTier = 'fast' | 'balanced' | 'quality';

export interface QualityPreset {
  rank: number;
  alpha: number;
  epochs: number;
  lr: number;
  gradCheckpoint: boolean;
  label: string;
  description: string;
}

/** Default caption template; `{tag}` is replaced with the user's style tag. */
export const CAPTION_TEMPLATE = 'a {tag} style song';

export const QUALITY_PRESETS: Record<QualityTier, QualityPreset> = {
  fast: {
    rank: 32,
    alpha: 64,
    epochs: 300,
    lr: 3e-4,
    gradCheckpoint: false,
    label: '快',
    description: '最快出片，保真度一般',
  },
  balanced: {
    rank: 64,
    alpha: 128,
    epochs: 600,
    lr: 3e-4,
    gradCheckpoint: false,
    label: '均',
    description: '速度与质量均衡',
  },
  quality: {
    rank: 128,
    alpha: 256,
    epochs: 1000,
    lr: 2e-4,
    gradCheckpoint: true,
    label: '质',
    description: '最高保真度，训练最久',
  },
};

export const VARIANT_DEFAULTS: Record<string, { shift: number; steps: number }> = {
  turbo: { shift: 3.0, steps: 8 },
  base: { shift: 1.0, steps: 50 },
  sft: { shift: 1.0, steps: 50 },
  // XL (4B DiT) family — keep in sync with acestep/training_v2/quick_presets.py
  xl: { shift: 3.0, steps: 8 },
  'xl-sft': { shift: 1.0, steps: 50 },
  'xl-base': { shift: 1.0, steps: 50 },
};

/** Render a caption from *template* by substituting `{tag}` with *tag*. */
export function renderCaption(template: string, tag: string): string {
  return (template || CAPTION_TEMPLATE).replace(/\{tag\}/g, tag || '');
}

/** Preview the caption that will be applied to every sample. */
export function previewCaption(quality: QualityTier, tag: string, template?: string): string {
  return renderCaption(template || CAPTION_TEMPLATE, tag || 'your_style');
}

export interface ResolvedParams {
  lora_rank: number;
  lora_alpha: number;
  lora_dropout: number;
  learning_rate: number;
  train_epochs: number;
  train_batch_size: number;
  gradient_accumulation: number;
  save_every_n_epochs: number;
  training_shift: number;
  training_seed: number;
  use_fp8: boolean;
  gradient_checkpointing: boolean;
}

const PARAM_KEYS: (keyof ResolvedParams)[] = [
  'lora_rank',
  'lora_alpha',
  'lora_dropout',
  'learning_rate',
  'train_epochs',
  'train_batch_size',
  'gradient_accumulation',
  'save_every_n_epochs',
  'training_shift',
  'training_seed',
  'use_fp8',
  'gradient_checkpointing',
];

/**
 * Merge a quality preset with optional advanced overrides + variant defaults.
 * Mirrors `quick_presets.resolve_training_params`.
 */
export function resolveTrainingParams(
  quality: QualityTier,
  advanced?: Record<string, any> | null,
  variant: string = 'turbo',
  tier: string = 'full',
): ResolvedParams {
  const preset = QUALITY_PRESETS[quality] || QUALITY_PRESETS.balanced;
  const variantDefaults = VARIANT_DEFAULTS[variant] || VARIANT_DEFAULTS.turbo;

  const params: ResolvedParams = {
    lora_rank: preset.rank,
    lora_alpha: preset.alpha,
    lora_dropout: 0.1,
    learning_rate: preset.lr,
    train_epochs: preset.epochs,
    train_batch_size: 1,
    gradient_accumulation: 4,
    save_every_n_epochs: 50,
    training_shift: variantDefaults.shift,
    training_seed: 42,
    use_fp8: false,
    gradient_checkpointing: preset.gradCheckpoint,
  };

  const adv = advanced || {};
  for (const key of PARAM_KEYS) {
    if (adv[key] !== undefined && adv[key] !== null) {
      // @ts-expect-error index assignment
      params[key] = adv[key];
    }
  }

  if (tier === 'fp8' || tier === 'low') {
    if (adv.use_fp8 === undefined) params.use_fp8 = true;
    if (adv.gradient_checkpointing === undefined) params.gradient_checkpointing = true;
  }

  return params;
}
