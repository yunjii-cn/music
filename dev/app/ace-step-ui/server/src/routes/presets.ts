import { Router, Response } from 'express';
import { pool } from '../db/pool.js';
import { authMiddleware, AuthenticatedRequest } from '../middleware/auth.js';
import { randomUUID } from 'crypto';

const router = Router();

const PRESET_TECHNICAL_PARAMS = [
  'customMode', 'instrumental', 'vocalLanguage', 'vocalGender',
  'bpm', 'duration', 'inferenceSteps', 'guidanceScale',
  'audioFormat', 'inferMethod', 'shift', 'useAdg',
  'taskType', 'ditModel', 'audioCoverStrength',
  'lmModel', 'lmBackend', 'lmTemperature', 'lmCfgScale',
  'lmTopK', 'lmTopP', 'lmNegativePrompt',
  'loraEnabled', 'loraScale',
  'cfgIntervalStart', 'cfgIntervalEnd',
  'customTimesteps', 'useCotMetas', 'useCotCaption', 'useCotLanguage',
  'autogen', 'allowLmBatch', 'getScores', 'getLrc',
  'scoreScale', 'lmBatchChunkSize', 'isFormatCaption',
  'randomSeed',
];

const BUILTIN_PRESETS = [
  {
    id: 'builtin-text2music-default',
    name: '文本生曲（默认）',
    description: '使用 turbo-shift3 模型进行文本生曲的默认设置',
    category: 'text2music',
    is_builtin: 1,
    params: {
      customMode: true,
      instrumental: false,
      vocalLanguage: 'en',
      bpm: 0,
      duration: -1,
      inferenceSteps: 12,
      guidanceScale: 9.0,
      randomSeed: true,
      audioFormat: 'mp3',
      inferMethod: 'ode',
      shift: 3.0,
      useAdg: true,
      taskType: 'text2music',
      ditModel: 'acestep-v15-turbo-shift3',
      lmModel: 'acestep-5Hz-lm-0.6B',
      lmBackend: 'pt',
      lmTemperature: 0.8,
      lmCfgScale: 2.2,
      lmTopK: 0,
      lmTopP: 0.92,
      lmNegativePrompt: 'NO USER INPUT',
      loraEnabled: false,
      loraScale: 1.0,
    },
  },
  {
    id: 'builtin-cover-lora',
    name: 'LoRA 翻唱',
    description: '使用 LoRA 音色翻唱的最佳设置。上传源音频获取旋律，加载 LoRA 获取音色。',
    category: 'cover',
    is_builtin: 1,
    params: {
      customMode: true,
      instrumental: false,
      vocalLanguage: 'zh',
      bpm: 0,
      duration: -1,
      inferenceSteps: 12,
      guidanceScale: 4.0,
      randomSeed: true,
      audioFormat: 'mp3',
      inferMethod: 'ode',
      shift: 3.0,
      useAdg: true,
      taskType: 'cover',
      audioCoverStrength: 1.0,
      ditModel: 'acestep-v15-turbo-shift3',
      lmModel: 'acestep-5Hz-lm-1.7B',
      lmBackend: 'pt',
      lmTemperature: 0.8,
      lmCfgScale: 2.2,
      lmTopK: 0,
      lmTopP: 0.92,
      lmNegativePrompt: 'NO USER INPUT',
      loraEnabled: true,
      loraScale: 0.9,
    },
  },
  {
    id: 'builtin-cover-high-fidelity',
    name: '高保真翻唱',
    description: '使用 SFT 模型的最高质量翻唱，更多推理步数和更高的引导强度。',
    category: 'cover',
    is_builtin: 1,
    params: {
      customMode: true,
      instrumental: false,
      vocalLanguage: 'zh',
      bpm: 0,
      duration: -1,
      inferenceSteps: 20,
      guidanceScale: 5.0,
      randomSeed: true,
      audioFormat: 'flac',
      inferMethod: 'ode',
      shift: 3.0,
      useAdg: true,
      taskType: 'cover',
      audioCoverStrength: 0.85,
      ditModel: 'acestep-v15-sft',
      lmModel: 'acestep-5Hz-lm-1.7B',
      lmBackend: 'pt',
      lmTemperature: 0.8,
      lmCfgScale: 2.2,
      lmTopK: 0,
      lmTopP: 0.92,
      lmNegativePrompt: 'NO USER INPUT',
      loraEnabled: true,
      loraScale: 0.8,
    },
  },
  {
    id: 'builtin-instrumental',
    name: '纯音乐',
    description: '生成无人声的纯音乐，适合背景音乐和BGM。',
    category: 'instrumental',
    is_builtin: 1,
    params: {
      customMode: true,
      instrumental: true,
      vocalLanguage: 'en',
      bpm: 120,
      duration: -1,
      inferenceSteps: 12,
      guidanceScale: 9.0,
      randomSeed: true,
      audioFormat: 'mp3',
      inferMethod: 'ode',
      shift: 3.0,
      useAdg: true,
      taskType: 'text2music',
      ditModel: 'acestep-v15-turbo-shift3',
      lmModel: 'acestep-5Hz-lm-0.6B',
      lmBackend: 'pt',
      lmTemperature: 0.8,
      lmCfgScale: 2.2,
      lmTopK: 0,
      lmTopP: 0.92,
      lmNegativePrompt: 'NO USER INPUT',
      loraEnabled: false,
      loraScale: 1.0,
    },
  },
  {
    id: 'builtin-audio2audio-style',
    name: '音频风格迁移',
    description: '保留结构的同时转换音频风格。使用 audio2audio 模式配合参考音频。',
    category: 'audio2audio',
    is_builtin: 1,
    params: {
      customMode: true,
      instrumental: false,
      vocalLanguage: 'en',
      bpm: 0,
      duration: -1,
      inferenceSteps: 12,
      guidanceScale: 5.0,
      randomSeed: true,
      audioFormat: 'mp3',
      inferMethod: 'ode',
      shift: 3.0,
      useAdg: true,
      taskType: 'audio2audio',
      audioCoverStrength: 0.7,
      ditModel: 'acestep-v15-turbo-shift3',
      lmModel: 'acestep-5Hz-lm-0.6B',
      lmBackend: 'pt',
      lmTemperature: 0.8,
      lmCfgScale: 2.2,
      lmTopK: 0,
      lmTopP: 0.92,
      lmNegativePrompt: 'NO USER INPUT',
      loraEnabled: false,
      loraScale: 1.0,
    },
  },
  {
    id: 'builtin-long-audio',
    name: '长音频生成',
    description: '使用 continuous 模型生成更长的音频轨道，稳定性极佳。',
    category: 'long',
    is_builtin: 1,
    params: {
      customMode: true,
      instrumental: false,
      vocalLanguage: 'en',
      bpm: 0,
      duration: 180,
      inferenceSteps: 12,
      guidanceScale: 9.0,
      randomSeed: true,
      audioFormat: 'mp3',
      inferMethod: 'ode',
      shift: 3.0,
      useAdg: true,
      taskType: 'text2music',
      ditModel: 'acestep-v15-turbo-continuous',
      lmModel: 'acestep-5Hz-lm-1.7B',
      lmBackend: 'pt',
      lmTemperature: 0.8,
      lmCfgScale: 2.2,
      lmTopK: 0,
      lmTopP: 0.92,
      lmNegativePrompt: 'NO USER INPUT',
      loraEnabled: false,
      loraScale: 1.0,
    },
  },
];

function filterTechnicalParams(params: Record<string, any>): Record<string, any> {
  const filtered: Record<string, any> = {};
  for (const key of PRESET_TECHNICAL_PARAMS) {
    if (params[key] !== undefined) {
      filtered[key] = params[key];
    }
  }
  return filtered;
}

async function ensureBuiltinPresets(userId: string): Promise<void> {
  for (const preset of BUILTIN_PRESETS) {
    const existing = await pool.query(
      'SELECT id FROM presets WHERE id = ?',
      [preset.id]
    );
    if (existing.rows.length === 0) {
      await pool.query(
        `INSERT INTO presets (id, user_id, name, description, is_builtin, category, params)
         VALUES (?, ?, ?, ?, ?, ?, ?)`,
        [
          preset.id,
          userId,
          preset.name,
          preset.description,
          preset.is_builtin,
          preset.category,
          JSON.stringify(preset.params),
        ]
      );
    }
  }
}

router.get('/', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const userId = req.user!.id;
    await ensureBuiltinPresets(userId);

    const result = await pool.query(
      `SELECT id, name, description, is_builtin, category, params, created_at, updated_at
       FROM presets
       WHERE user_id = ?
       ORDER BY is_builtin DESC, category ASC, name ASC`,
      [userId]
    );

    const presets = result.rows.map(row => ({
      ...row,
      is_builtin: Boolean(row.is_builtin),
      params: typeof row.params === 'string' ? JSON.parse(row.params) : row.params,
    }));

    res.json({ presets });
  } catch (error) {
    console.error('Get presets error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.post('/', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const userId = req.user!.id;
    const { name, description, category, params } = req.body;

    if (!name || !name.trim()) {
      res.status(400).json({ error: 'Preset name is required' });
      return;
    }
    if (!params || typeof params !== 'object') {
      res.status(400).json({ error: 'Preset params are required' });
      return;
    }

    const filteredParams = filterTechnicalParams(params);

    const id = randomUUID();
    const result = await pool.query(
      `INSERT INTO presets (id, user_id, name, description, category, params)
       VALUES (?, ?, ?, ?, ?, ?)
       RETURNING *`,
      [id, userId, name.trim(), description?.trim() || null, category || 'custom', JSON.stringify(filteredParams)]
    );

    const preset = result.rows[0];
    res.status(201).json({
      preset: {
        ...preset,
        is_builtin: Boolean(preset.is_builtin),
        params: typeof preset.params === 'string' ? JSON.parse(preset.params) : preset.params,
      },
    });
  } catch (error) {
    console.error('Create preset error:', error);
    res.status(500).json({ error: 'Failed to create preset' });
  }
});

router.patch('/:id', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const check = await pool.query(
      'SELECT user_id, is_builtin FROM presets WHERE id = ?',
      [req.params.id]
    );
    if (check.rows.length === 0) {
      res.status(404).json({ error: 'Preset not found' });
      return;
    }
    if (check.rows[0].user_id !== req.user!.id) {
      res.status(403).json({ error: 'Access denied' });
      return;
    }
    if (Boolean(check.rows[0].is_builtin)) {
      res.status(400).json({ error: 'Cannot modify built-in presets' });
      return;
    }

    const { name, description, category, params } = req.body;
    const updates: string[] = [];
    const values: unknown[] = [];

    if (name !== undefined) {
      updates.push('name = ?');
      values.push(name.trim());
    }
    if (description !== undefined) {
      updates.push('description = ?');
      values.push(description?.trim() || null);
    }
    if (category !== undefined) {
      updates.push('category = ?');
      values.push(category);
    }
    if (params !== undefined) {
      updates.push('params = ?');
      values.push(JSON.stringify(filterTechnicalParams(params)));
    }

    if (updates.length === 0) {
      res.status(400).json({ error: 'No fields to update' });
      return;
    }

    updates.push("updated_at = datetime('now')");
    values.push(req.params.id);

    const result = await pool.query(
      `UPDATE presets SET ${updates.join(', ')} WHERE id = ? RETURNING *`,
      values
    );

    const preset = result.rows[0];
    res.json({
      preset: {
        ...preset,
        is_builtin: Boolean(preset.is_builtin),
        params: typeof preset.params === 'string' ? JSON.parse(preset.params) : preset.params,
      },
    });
  } catch (error) {
    console.error('Update preset error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.delete('/:id', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const check = await pool.query(
      'SELECT user_id, is_builtin FROM presets WHERE id = ?',
      [req.params.id]
    );
    if (check.rows.length === 0) {
      res.status(404).json({ error: 'Preset not found' });
      return;
    }
    if (check.rows[0].user_id !== req.user!.id) {
      res.status(403).json({ error: 'Access denied' });
      return;
    }
    if (Boolean(check.rows[0].is_builtin)) {
      res.status(400).json({ error: 'Cannot delete built-in presets' });
      return;
    }

    await pool.query('DELETE FROM presets WHERE id = ?', [req.params.id]);
    res.json({ success: true });
  } catch (error) {
    console.error('Delete preset error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

export default router;
