import { Router, Response } from 'express';
import multer from 'multer';
import path from 'path';
import { fileURLToPath } from 'url';
import { pool } from '../db/pool.js';
import { generateUUID } from '../db/sqlite.js';
import { authMiddleware, AuthenticatedRequest } from '../middleware/auth.js';
import {
  getAudioStream,
  discoverEndpoints,
  checkSpaceHealth,
  downloadAudioToBuffer,
  getJobRawResponse,
  resolvePythonPath,
} from '../services/acestep.js';
import { config } from '../config/index.js';
import { getStorageProvider } from '../services/storage/factory.js';

const __filename_gen = fileURLToPath(import.meta.url);
const __dirname_gen = path.dirname(__filename_gen);
const AUDIO_DIR = path.join(__dirname_gen, '../../public/audio');

async function fetchWithTimeout(url: string, options: RequestInit, timeoutMs = 30000): Promise<globalThis.Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  const mergedOptions: RequestInit = { ...options, signal: controller.signal };
  try {
    const response: globalThis.Response = await fetch(url, mergedOptions);
    clearTimeout(timer);
    return response;
  } catch (err) {
    clearTimeout(timer);
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new Error(`Request to ${url} timed out after ${timeoutMs}ms`);
    }
    throw err;
  }
}

function resolveAudioPath(audioUrl: string): string {
  if (audioUrl.startsWith('/audio/')) {
    return path.join(AUDIO_DIR, audioUrl.replace('/audio/', ''));
  }
  if (audioUrl.startsWith('http')) {
    try {
      const parsed = new URL(audioUrl);
      if (parsed.pathname.startsWith('/audio/')) {
        return path.join(AUDIO_DIR, parsed.pathname.replace('/audio/', ''));
      }
    } catch {
      // fall through
    }
  }
  // Handle uploaded URL keys (e.g. "references/{userId}/...")
  if (audioUrl.startsWith('references/')) {
    return path.join(AUDIO_DIR, audioUrl);
  }
  return audioUrl;
}

const router = Router();

const audioUpload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 25 * 1024 * 1024 }, // 25MB max
  fileFilter: (_req, file, cb) => {
    const allowedTypes = [
      'audio/mpeg',
      'audio/mp3', // Alternative MIME type for MP3
      'audio/mpeg3',
      'audio/x-mpeg-3',
      'audio/wav',
      'audio/x-wav',
      'audio/flac',
      'audio/x-flac',
      'audio/mp4',
      'audio/x-m4a',
      'audio/aac',
      'audio/ogg',
      'audio/webm',
      'video/mp4',
    ];

    // Also check file extension as fallback
    const allowedExtensions = ['.mp3', '.wav', '.flac', '.m4a', '.mp4', '.aac', '.ogg', '.webm', '.opus'];
    const fileExt = file.originalname.toLowerCase().match(/\.[^.]+$/)?.[0];

    if (allowedTypes.includes(file.mimetype) || (fileExt && allowedExtensions.includes(fileExt))) {
      cb(null, true);
    } else {
      cb(new Error(`Invalid file type. Only common audio formats are allowed. Received: ${file.mimetype} (${file.originalname})`));
    }
  }
});

interface GenerateBody {
  // Mode
  customMode: boolean;

  // Simple Mode
  songDescription?: string;

  // Custom Mode
  lyrics: string;
  style: string;
  title: string;

  // Model Selection
  ditModel?: string;

  // Common
  instrumental: boolean;
  vocalLanguage?: string;

  // Music Parameters
  duration?: number;
  bpm?: number;
  keyScale?: string;
  timeSignature?: string;

  // Generation Settings
  inferenceSteps?: number;
  guidanceScale?: number;
  batchSize?: number;
  randomSeed?: boolean;
  seed?: number;
  thinking?: boolean;
  audioFormat?: 'mp3' | 'flac';
  inferMethod?: 'ode' | 'sde';
  shift?: number;

  // LM Parameters
  lmTemperature?: number;
  lmCfgScale?: number;
  lmTopK?: number;
  lmTopP?: number;
  lmNegativePrompt?: string;
  lmBackend?: 'pt' | 'vllm';
  lmModel?: string;

  // Expert Parameters
  referenceAudioUrl?: string;
  sourceAudioUrl?: string;
  referenceAudioTitle?: string;
  sourceAudioTitle?: string;
  audioCodes?: string;
  repaintingStart?: number;
  repaintingEnd?: number;
  instruction?: string;
  audioCoverStrength?: number;
  coverNoiseStrength?: number;
  enableNormalization?: boolean;
  normalizationDb?: number;
  latentShift?: number;
  latentRescale?: number;
  taskType?: string;
  useAdg?: boolean;
  cfgIntervalStart?: number;
  cfgIntervalEnd?: number;
  customTimesteps?: string;
  useCotMetas?: boolean;
  useCotCaption?: boolean;
  useCotLanguage?: boolean;
  autogen?: boolean;
  constrainedDecodingDebug?: boolean;
  allowLmBatch?: boolean;
  getScores?: boolean;
  getLrc?: boolean;
  scoreScale?: number;
  lmBatchChunkSize?: number;
  trackName?: string;
  completeTrackClasses?: string[];
  isFormatCaption?: boolean;
  loraLoaded?: boolean;
}

router.post('/upload-audio', authMiddleware, audioUpload.single('audio'), async (req: AuthenticatedRequest, res: Response) => {
  try {
    if (!req.file) {
      res.status(400).json({ error: 'Audio file is required' });
      return;
    }

    const storage = getStorageProvider();
    const extFromName = path.extname(req.file.originalname || '').toLowerCase();
    const extFromType = (() => {
      switch (req.file.mimetype) {
        case 'audio/mpeg':
          return '.mp3';
        case 'audio/wav':
        case 'audio/x-wav':
          return '.wav';
        case 'audio/flac':
        case 'audio/x-flac':
          return '.flac';
        case 'audio/ogg':
          return '.ogg';
        case 'audio/mp4':
        case 'audio/x-m4a':
        case 'audio/aac':
          return '.m4a';
        case 'audio/webm':
          return '.webm';
        case 'video/mp4':
          return '.mp4';
        default:
          return '';
      }
    })();
    const ext = extFromName || extFromType || '.audio';
    const key = `references/${req.user!.id}/${Date.now()}-${generateUUID()}${ext}`;
    const storedKey = await storage.upload(key, req.file.buffer, req.file.mimetype);
    const publicUrl = storage.getPublicUrl(storedKey);

    res.json({ url: publicUrl, key: storedKey });
  } catch (error) {
    console.error('Upload reference audio error:', error);
    res.status(500).json({ error: 'Failed to upload audio' });
  }
});

router.post('/', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  let localJobId: string | null = null;
  try {
    const {
      customMode,
      songDescription,
      lyrics,
      style,
      title,
      ditModel,
      instrumental,
      vocalLanguage,
      duration,
      bpm,
      keyScale,
      timeSignature,
      inferenceSteps,
      guidanceScale,
      batchSize,
      randomSeed,
      seed,
      thinking,
      audioFormat,
      inferMethod,
      shift,
      lmTemperature,
      lmCfgScale,
      lmTopK,
      lmTopP,
      lmNegativePrompt,
      lmBackend,
      lmModel,
      referenceAudioUrl,
      sourceAudioUrl,
      referenceAudioTitle,
      sourceAudioTitle,
      audioCodes,
      repaintingStart,
      repaintingEnd,
      instruction,
      audioCoverStrength,
      coverNoiseStrength,
      enableNormalization,
      normalizationDb,
      latentShift,
      latentRescale,
      taskType,
      useAdg,
      cfgIntervalStart,
      cfgIntervalEnd,
      customTimesteps,
      useCotMetas,
      useCotCaption,
      useCotLanguage,
      autogen,
      constrainedDecodingDebug,
      allowLmBatch,
      getScores,
      getLrc,
      scoreScale,
      lmBatchChunkSize,
      trackName,
      completeTrackClasses,
      isFormatCaption,
      loraLoaded,
    } = req.body as GenerateBody;

    if (!customMode && !songDescription) {
      res.status(400).json({ error: 'Song description required for simple mode' });
      return;
    }

    if (customMode && !style && !lyrics && !referenceAudioUrl) {
      res.status(400).json({ error: 'Style, lyrics, or reference audio required for custom mode' });
      return;
    }

    // Guard: cover / audio2audio require a source audio or audio codes.
    // Without this, src_audio_path is silently omitted and the Python side
    // falls back to a silent latent -> pure noise output.
    if ((taskType === 'cover' || taskType === 'audio2audio') && !sourceAudioUrl && !audioCodes) {
      res.status(400).json({ error: `task_type='${taskType}' requires a source audio or audio codes` });
      return;
    }

    const params = {
      customMode,
      songDescription,
      lyrics,
      style,
      title,
      ditModel,
      instrumental,
      vocalLanguage,
      duration,
      bpm,
      keyScale,
      timeSignature,
      inferenceSteps,
      guidanceScale,
      batchSize,
      randomSeed,
      seed,
      thinking,
      audioFormat,
      inferMethod,
      shift,
      lmTemperature,
      lmCfgScale,
      lmTopK,
      lmTopP,
      lmNegativePrompt,
      lmBackend,
      lmModel,
      referenceAudioUrl,
      sourceAudioUrl,
      referenceAudioTitle,
      sourceAudioTitle,
      audioCodes,
      repaintingStart,
      repaintingEnd,
      instruction,
      audioCoverStrength,
      coverNoiseStrength,
      enableNormalization,
      normalizationDb,
      latentShift,
      latentRescale,
      taskType,
      useAdg,
      cfgIntervalStart,
      cfgIntervalEnd,
      customTimesteps,
      useCotMetas,
      useCotCaption,
      useCotLanguage,
      autogen,
      constrainedDecodingDebug,
      allowLmBatch,
      getScores,
      getLrc,
      scoreScale,
      lmBatchChunkSize,
      trackName,
      completeTrackClasses,
      isFormatCaption,
      loraLoaded,
    };

    // Create job record in database
    localJobId = generateUUID();
    await pool.query(
      `INSERT INTO generation_jobs (id, user_id, status, params, created_at, updated_at)
       VALUES (?, ?, 'queued', ?, datetime('now'), datetime('now'))`,
      [localJobId, req.user!.id, JSON.stringify(params)]
    );

    // Call 8001 API to start generation
    if (params.taskType === 'cover') {
      const resolvedSrc = params.sourceAudioUrl ? resolveAudioPath(params.sourceAudioUrl) : '(none)';
      console.log(`[Cover] sourceAudioUrl: ${params.sourceAudioUrl}, resolved: ${resolvedSrc}, coverNoiseStrength: ${params.coverNoiseStrength}`);
    }
    const acestepResponse = await fetchWithTimeout(`${config.acestep.apiUrl}/release_task`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': process.env.ACESTEP_API_KEY || '',
      },
      body: JSON.stringify({
        prompt: params.customMode ? params.style : (params.songDescription || params.style),
        lyrics: params.instrumental ? '' : (params.lyrics || ''),
        thinking: params.thinking || false,
        dit_model: params.ditModel,
        bpm: params.bpm,
        key_scale: params.keyScale,
        time_signature: params.timeSignature,
        audio_duration: params.duration,
        vocal_language: params.vocalLanguage || 'en',
        inference_steps: params.inferenceSteps || 8,
        guidance_scale: params.guidanceScale || 10.0,
        use_random_seed: params.randomSeed !== false,
        seed: params.seed || -1,
        batch_size: params.batchSize || 1,
        audio_code_string: params.audioCodes,
        repainting_start: params.repaintingStart || 0.0,
        repainting_end: params.repaintingEnd,
        instruction: params.instruction,
        ...(params.referenceAudioUrl ? { reference_audio_path: resolveAudioPath(params.referenceAudioUrl) } : {}),
        ...(params.sourceAudioUrl ? {         src_audio_path: resolveAudioPath(params.sourceAudioUrl) } : {}),
        audio_cover_strength: params.audioCoverStrength ?? 1.0,
        cover_noise_strength: params.taskType === 'cover' ? (params.coverNoiseStrength ?? 0.3) : 0.0,
        enable_normalization: params.enableNormalization !== undefined ? params.enableNormalization : true,
        normalization_db: params.normalizationDb !== undefined ? params.normalizationDb : -1.0,
        latent_shift: params.latentShift || 0.0,
        latent_rescale: params.latentRescale || 1.0,
        task_type: params.taskType || 'text2music',
        ...(params.trackName ? { track_name: params.trackName } : {}),
        ...(params.completeTrackClasses?.length ? { track_classes: params.completeTrackClasses } : {}),
        use_adg: params.useAdg || false,
        cfg_interval_start: params.cfgIntervalStart || 0.0,
        cfg_interval_end: params.cfgIntervalEnd || 1.0,
        infer_method: params.inferMethod || 'ode',
        shift: params.shift,
        ...(params.customTimesteps ? { custom_timesteps: params.customTimesteps } : {}),
        audio_format: params.audioFormat || 'mp3',
        use_cot_caption: params.thinking ? (params.useCotCaption !== false) : false,
        use_cot_language: params.thinking ? (params.useCotLanguage !== false) : false,
        use_cot_metas: false,
        ...(params.thinking ? {
          lm_model_path: params.lmModel || undefined,
          lm_backend: params.lmBackend || 'pt',
          lm_temperature: params.lmTemperature,
          lm_cfg_scale: params.lmCfgScale,
          lm_top_k: params.lmTopK,
          lm_top_p: params.lmTopP,
          lm_negative_prompt: params.lmNegativePrompt,
        } : {}),
      }),
    }, 300000);

    if (!acestepResponse.ok) {
      const error = await acestepResponse.json().catch(() => ({ error: 'Generation failed' }));
      const msg = error.error || error.message || 'Failed to start generation';
      try {
        await pool.query(
          `UPDATE generation_jobs SET status = 'failed', error = ?, updated_at = datetime('now') WHERE id = ?`,
          [String(msg), localJobId]
        );
      } catch (dbErr) {
        console.error('Failed to mark generation job failed:', dbErr);
      }
      throw new Error(msg);
    }

    const acestepResult = await acestepResponse.json();
    const taskId = acestepResult.data?.task_id || acestepResult.task_id;

    if (!taskId) {
      throw new Error('No task ID returned from ACE-Step API');
    }

    // Update job with ACE-Step task ID
    await pool.query(
      `UPDATE generation_jobs SET acestep_task_id = ?, status = 'running', updated_at = datetime('now') WHERE id = ?`,
      [taskId, localJobId]
    );

    res.json({
      jobId: localJobId,
      status: 'queued',
      queuePosition: 1,
    });
  } catch (error) {
    console.error('Generate error:', error);

    if (localJobId) {
      try {
        await pool.query(
          `UPDATE generation_jobs SET status = 'failed', error = ?, updated_at = datetime('now') WHERE id = ?`,
          [String((error as Error)?.message || 'Generation failed'), localJobId]
        );
      } catch (dbErr) {
        console.error('Failed to mark generation job failed:', dbErr);
      }
    }

    res.status(500).json({ error: (error as Error).message || 'Generation failed' });
  }
});

router.get('/status/:jobId', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const jobResult = await pool.query(
      `SELECT id, user_id, acestep_task_id, status, params, result, error, created_at
       FROM generation_jobs
       WHERE id = ?`,
      [req.params.jobId]
    );

    if (jobResult.rows.length === 0) {
      res.status(404).json({ error: 'Job not found' });
      return;
    }

    const job = jobResult.rows[0];

    if (job.user_id !== req.user!.id) {
      res.status(403).json({ error: 'Access denied' });
      return;
    }

    // If job is still running, check ACE-Step status
    if (['pending', 'queued', 'running'].includes(job.status) && job.acestep_task_id) {
      try {
        const createdAtMs = (() => {
          try {
            const d = new Date(job.created_at);
            const t = d.getTime();
            return Number.isFinite(t) ? t : Date.now();
          } catch {
            return Date.now();
          }
        })();
        const jobAgeMs = Date.now() - createdAtMs;

        // Query 8001 API for task status
        const queryResponse = await fetchWithTimeout(`${config.acestep.apiUrl}/query_result`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'x-api-key': process.env.ACESTEP_API_KEY || '',
          },
          body: JSON.stringify({
            task_id_list: [job.acestep_task_id],
          }),
        });

        if (!queryResponse.ok) {
          const raw = await queryResponse.text().catch(() => '');
          const msg = `ACE-Step status query failed (${queryResponse.status})` + (raw ? `: ${raw.slice(0, 200)}` : '');
          const shouldFail = (queryResponse.status >= 400 && queryResponse.status < 500) || jobAgeMs > 2 * 60 * 1000;
          if (shouldFail) {
            try {
              await pool.query(
                `UPDATE generation_jobs SET status = 'failed', error = ?, updated_at = datetime('now') WHERE id = ?`,
                [msg, req.params.jobId]
              );
            } catch (dbErr) {
              console.error('Failed to mark job failed:', dbErr);
            }
            res.json({
              jobId: req.params.jobId,
              status: 'failed',
              result: null,
              error: msg,
            });
            return;
          }

          throw new Error(msg);
        }

        const queryResult = await queryResponse.json();

        // Response format: { code: 200, data: [{ task_id, result, status }] }
        const dataList = queryResult.data || queryResult.data_list || queryResult;
        const taskData = Array.isArray(dataList) ? dataList[0] : null;

        if (!taskData) {
          console.error('Failed to parse task data. Full response:', JSON.stringify(queryResult, null, 2));
          console.error('Looking for task_id:', job.acestep_task_id);
          const msg = 'No task data in response';
          if (jobAgeMs > 2 * 60 * 1000) {
            try {
              await pool.query(
                `UPDATE generation_jobs SET status = 'failed', error = ?, updated_at = datetime('now') WHERE id = ?`,
                [msg, req.params.jobId]
              );
            } catch (dbErr) {
              console.error('Failed to mark job failed:', dbErr);
            }
            res.json({
              jobId: req.params.jobId,
              status: 'failed',
              result: null,
              error: msg,
            });
            return;
          }
          throw new Error(msg);
        }

        console.log('Task data:', JSON.stringify(taskData, null, 2));

        // Map ACE-Step status codes to our status
        const statusMap: Record<number, string> = {
          0: 'running',
          1: 'succeeded',
          2: 'failed',
        };

        // Parse result data
        let resultData = null;
        if (taskData.status === 1 && taskData.result) {
          const parsedResults = JSON.parse(taskData.result);
          const audioUrls: string[] = [];
          let firstResult = null;

          // Process all results from batch
          for (let i = 0; i < parsedResults.length; i++) {
            const parsedResult = parsedResults[i];
            if (i === 0) firstResult = parsedResult;

            // Convert path to full URL
            let audioUrl = parsedResult.file;
            console.log(`[Batch ${i + 1}/${parsedResults.length}] Original file path:`, audioUrl);

            if (audioUrl) {
              if (audioUrl.startsWith('/v1/audio')) {
                audioUrl = `${config.acestep.apiUrl}${audioUrl}`;
                console.log(`[Batch ${i + 1}] Prepended domain to API path:`, audioUrl);
              } else if (!audioUrl.startsWith('http')) {
                audioUrl = `${config.acestep.apiUrl}/v1/audio?path=${encodeURIComponent(audioUrl)}`;
                console.log(`[Batch ${i + 1}] Converted file path to API URL:`, audioUrl);
              }
              audioUrls.push(audioUrl);
            }
          }

          resultData = {
            audioUrls,
            duration: firstResult?.metas?.duration,
            bpm: firstResult?.metas?.bpm,
            keyScale: firstResult?.metas?.keyscale,
            timeSignature: firstResult?.metas?.timesignature,
            ditModel: firstResult?.dit_model,
            seedValue: firstResult?.seed_value,
            generationInfo: firstResult?.generation_info,
            lmModel: firstResult?.lm_model,
            status: 'succeeded',
          };
        }

        const aceStatus = {
          status: statusMap[taskData.status] || 'running',
          result: resultData,
          error: taskData.status === 2 ? 'Generation failed' : undefined,
          queuePosition: undefined,
          etaSeconds: undefined,
          progress: undefined,
          stage: undefined,
        };

        if (aceStatus.status !== job.status) {
          let updateQuery = `UPDATE generation_jobs SET status = ?, updated_at = datetime('now')`;
          const updateParams: unknown[] = [aceStatus.status];

          if (aceStatus.status === 'succeeded' && aceStatus.result) {
            updateQuery += `, result = ?`;
            updateParams.push(JSON.stringify(aceStatus.result));
          } else if (aceStatus.status === 'failed' && aceStatus.error) {
            updateQuery += `, error = ?`;
            updateParams.push(aceStatus.error);
          }

          updateQuery += ` WHERE id = ?`;
          updateParams.push(req.params.jobId);

          await pool.query(updateQuery, updateParams);

          // If succeeded, create song records
          if (aceStatus.status === 'succeeded' && aceStatus.result) {
            const params = typeof job.params === 'string' ? JSON.parse(job.params) : job.params;

            const durationVal = (aceStatus.result as any).duration != null && (aceStatus.result as any).duration > 0
              ? (aceStatus.result as any).duration
              : (params.duration && params.duration > 0 ? params.duration : 120);
            const bpmVal = (aceStatus.result as any).bpm ?? params.bpm;
            const keyScaleVal = (aceStatus.result as any).keyScale ?? params.keyScale;
            const normalizeTimeSignature = (v: unknown) => {
              if (v == null) return undefined;
              if (typeof v === 'string') {
                const s = v.trim();
                if (!s) return undefined;
                if (s.includes('/')) return s;
                const n = Number(s);
                return Number.isFinite(n) ? `${n}/4` : s;
              }
              if (typeof v === 'number' && Number.isFinite(v)) {
                return `${v}/4`;
              }
              const s = String(v);
              return s.includes('/') ? s : s;
            };
            const timeSignatureVal = normalizeTimeSignature((aceStatus.result as any).timeSignature ?? params.timeSignature);
            const ditModelVal = (aceStatus.result as any).ditModel ?? params.ditModel ?? 'acestep-v15-sft';
            const lmModelVal = (aceStatus.result as any).lmModel ?? params.lmModel;

            const seedText = (aceStatus.result as any).seedValue != null
              ? String((aceStatus.result as any).seedValue)
              : undefined;
            const seed = (() => {
              if (!seedText) return undefined;
              const first = seedText.split(',')[0]?.trim();
              if (!first) return undefined;
              const n = Number(first);
              return Number.isFinite(n) ? n : undefined;
            })();

            const generationInfo = (aceStatus.result as any).generationInfo;
            const inferenceSteps = (() => {
              if (typeof generationInfo !== 'string') return undefined;
              const m = generationInfo.match(/Steps:\s*(\d+)/i);
              if (!m?.[1]) return undefined;
              const n = Number(m[1]);
              return Number.isFinite(n) ? n : undefined;
            })();

            const generationParamsToStore = {
              ...params,
              duration: durationVal,
              bpm: bpmVal,
              keyScale: keyScaleVal,
              timeSignature: timeSignatureVal,
              ditModel: ditModelVal,
              ...(lmModelVal != null ? { lmModel: lmModelVal } : {}),
              ...(seedText != null ? { seedText } : {}),
              ...(seed != null ? { seed } : {}),
              ...(inferenceSteps != null ? { inferenceSteps } : {}),
              ...(generationInfo != null ? { generationInfo } : {}),
            };

            const audioUrls = aceStatus.result.audioUrls.filter((url: string) =>
              url.endsWith('.mp3') || url.endsWith('.flac')
            );
            const localPaths: string[] = [];
            const storage = getStorageProvider();

            for (let i = 0; i < audioUrls.length; i++) {
              const audioUrl = audioUrls[i];
              const now = new Date();
              const dateSuffix = `${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}-${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}`;
              const variationSuffix = audioUrls.length > 1 ? ` (v${i + 1})` : '';
              const songTitle = (params.title || 'Untitled') + ` ${dateSuffix}` + variationSuffix;

              const songId = generateUUID();

              try {
                const { buffer } = await downloadAudioToBuffer(audioUrl);
                const ext = audioUrl.includes('.flac') ? '.flac' : '.mp3';
                const storageKey = `${req.user!.id}/${songId}${ext}`;
                await storage.upload(storageKey, buffer, `audio/${ext.slice(1)}`);
                const storedPath = storage.getPublicUrl(storageKey);

                await pool.query(
                  `INSERT INTO songs (id, user_id, title, lyrics, style, caption, audio_url,
                                      duration, bpm, key_scale, time_signature, tags, is_public, model, generation_params,
                                      created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, datetime('now'), datetime('now'))`,
                  [
                    songId,
                    req.user!.id,
                    songTitle,
                    params.instrumental ? '[Instrumental]' : params.lyrics,
                    params.style,
                    params.style,
                    storedPath,
                    durationVal,
                    bpmVal,
                    keyScaleVal,
                    timeSignatureVal,
                    JSON.stringify([]),
                    ditModelVal,
                    JSON.stringify(generationParamsToStore),
                  ]
                );

                localPaths.push(storedPath);
              } catch (downloadError) {
                console.error(`Failed to download audio ${i + 1}:`, downloadError);
                // Still create song record with remote URL
                await pool.query(
                  `INSERT INTO songs (id, user_id, title, lyrics, style, caption, audio_url,
                                      duration, bpm, key_scale, time_signature, tags, is_public, model, generation_params,
                                      created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, datetime('now'), datetime('now'))`,
                  [
                    songId,
                    req.user!.id,
                    songTitle,
                    params.instrumental ? '[Instrumental]' : params.lyrics,
                    params.style,
                    params.style,
                    audioUrl,
                    durationVal,
                    bpmVal,
                    keyScaleVal,
                    timeSignatureVal,
                    JSON.stringify([]),
                    ditModelVal,
                    JSON.stringify(generationParamsToStore),
                  ]
                );
                localPaths.push(audioUrl);
              }
            }

            aceStatus.result.audioUrls = localPaths;
          }
        }

        res.json({
          jobId: req.params.jobId,
          status: aceStatus.status,
          queuePosition: aceStatus.queuePosition,
          etaSeconds: aceStatus.etaSeconds,
          progress: aceStatus.progress,
          stage: aceStatus.stage,
          result: aceStatus.result,
          error: aceStatus.error,
        });
        return;
      } catch (aceError) {
        console.error('ACE-Step status check error:', aceError);

        const createdAtMs = (() => {
          try {
            const d = new Date(job.created_at);
            const t = d.getTime();
            return Number.isFinite(t) ? t : Date.now();
          } catch {
            return Date.now();
          }
        })();
        const jobAgeMs = Date.now() - createdAtMs;
        if (jobAgeMs > 10 * 60 * 1000) {
          const msg = aceError instanceof Error ? aceError.message : 'ACE-Step status check error';
          try {
            await pool.query(
              `UPDATE generation_jobs SET status = 'failed', error = ?, updated_at = datetime('now') WHERE id = ?`,
              [String(msg), req.params.jobId]
            );
          } catch (dbErr) {
            console.error('Failed to mark job failed:', dbErr);
          }

          res.json({
            jobId: req.params.jobId,
            status: 'failed',
            result: null,
            error: String(msg),
          });
          return;
        }
      }
    }

    // Return stored status
    res.json({
      jobId: req.params.jobId,
      status: job.status,
      progress: undefined,
      stage: undefined,
      result: job.result && typeof job.result === 'string' ? JSON.parse(job.result) : job.result,
      error: job.error,
    });
  } catch (error) {
    console.error('Status check error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.delete('/job/:jobId', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const jobId = req.params.jobId;
    if (!jobId) {
      res.status(400).json({ error: 'Job ID is required' });
      return;
    }

    const jobResult = await pool.query(
      `SELECT id, user_id
       FROM generation_jobs
       WHERE id = ?`,
      [jobId]
    );

    if (jobResult.rows.length === 0) {
      res.status(404).json({ error: 'Job not found' });
      return;
    }

    const job = jobResult.rows[0];
    if (job.user_id !== req.user!.id) {
      res.status(403).json({ error: 'Access denied' });
      return;
    }

    await pool.query(
      `DELETE FROM generation_jobs
       WHERE id = ?`,
      [jobId]
    );

    res.json({ success: true });
  } catch (error) {
    console.error('Delete job error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Audio proxy endpoint
router.get('/audio', async (req, res: Response) => {
  try {
    const audioPath = req.query.path as string;
    if (!audioPath) {
      res.status(400).json({ error: 'Path required' });
      return;
    }

    const audioResponse = await getAudioStream(audioPath);

    if (!audioResponse.ok) {
      res.status(audioResponse.status).json({ error: 'Failed to fetch audio' });
      return;
    }

    const contentType = audioResponse.headers.get('content-type');
    if (contentType) {
      res.setHeader('Content-Type', contentType);
    }

    const contentLength = audioResponse.headers.get('content-length');
    if (contentLength) {
      res.setHeader('Content-Length', contentLength);
    }

    const reader = audioResponse.body?.getReader();
    if (!reader) {
      res.status(500).json({ error: 'Failed to read audio stream' });
      return;
    }

    const pump = async (): Promise<void> => {
      const { done, value } = await reader.read();
      if (done) {
        res.end();
        return;
      }
      res.write(value);
      return pump();
    };

    await pump();
  } catch (error) {
    console.error('Audio proxy error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.get('/history', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const result = await pool.query(
      `SELECT id, acestep_task_id, status, params, result, error, created_at
       FROM generation_jobs
       WHERE user_id = ?
       ORDER BY created_at DESC
       LIMIT 50`,
      [req.user!.id]
    );

    res.json({ jobs: result.rows });
  } catch (error) {
    console.error('Get history error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.get('/models', async (_req, res: Response) => {
  try {
    const modelsResponse = await fetchWithTimeout(`${config.acestep.apiUrl}/api/generate/models`, {
      headers: {
        'x-api-key': process.env.ACESTEP_API_KEY || '',
      },
    });

    if (!modelsResponse.ok) {
      res.status(modelsResponse.status).json({ error: 'Failed to fetch models' });
      return;
    }

    const result = await modelsResponse.json();
    res.json(result.data || result);
  } catch (error: any) {
    const isConnRefused = error?.cause?.code === 'ECONNREFUSED' ||
      error?.code === 'ECONNREFUSED';
    if (isConnRefused) {
      console.warn('Models proxy: ACE-Step backend not reachable yet');
      res.status(503).json({ error: 'ACE-Step 后端暂未启动', backend_unavailable: true });
    } else {
      console.error('Models proxy error:', error);
      res.status(500).json({ error: 'Failed to fetch models from backend' });
    }
  }
});

router.get('/models/verify', async (req, res: Response) => {
  try {
    const modelName = req.query.model_name as string;
    if (!modelName) {
      res.status(400).json({ error: 'model_name parameter is required' });
      return;
    }

    const verifyResponse = await fetchWithTimeout(
      `${config.acestep.apiUrl}/api/generate/models/verify?model_name=${encodeURIComponent(modelName)}`,
      {
        headers: {
          'x-api-key': process.env.ACESTEP_API_KEY || '',
        },
      }
    );

    if (!verifyResponse.ok) {
      res.status(verifyResponse.status).json({ error: 'Failed to verify model' });
      return;
    }

    const result = await verifyResponse.json();
    res.json(result.data || result);
  } catch (error: any) {
    const isConnRefused = error?.cause?.code === 'ECONNREFUSED' ||
      error?.code === 'ECONNREFUSED';
    if (isConnRefused) {
      console.warn('Model verify proxy: ACE-Step backend not reachable yet');
      res.status(503).json({ error: 'ACE-Step 后端暂未启动', backend_unavailable: true });
    } else {
      console.error('Model verify proxy error:', error);
      res.status(500).json({ error: 'Failed to verify model from backend' });
    }
  }
});

router.get('/endpoints', authMiddleware, async (_req: AuthenticatedRequest, res: Response) => {
  try {
    const endpoints = await discoverEndpoints();
    res.json({ endpoints });
  } catch (error) {
    console.error('Discover endpoints error:', error);
    res.status(500).json({ error: 'Failed to discover endpoints' });
  }
});

router.get('/health', async (_req, res: Response) => {
  try {
    const healthy = await checkSpaceHealth();
    res.json({ healthy });
  } catch (error) {
    res.json({ healthy: false, error: (error as Error).message });
  }
});

router.get('/limits', async (_req, res: Response) => {
  try {
    const { spawn } = await import('child_process');
    const ACESTEP_DIR = process.env.ACESTEP_PATH || path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../../../ACE-Step-1.5');
    const __filename = fileURLToPath(import.meta.url);
    const __dirname = path.dirname(__filename);
    const SCRIPTS_DIR = path.join(__dirname, '../../scripts');
    const LIMITS_SCRIPT = path.join(SCRIPTS_DIR, 'get_limits.py');
    const pythonPath = resolvePythonPath(ACESTEP_DIR);

    const result = await new Promise<{ success: boolean; data?: any; error?: string }>((resolve) => {
      const proc = spawn(pythonPath, [LIMITS_SCRIPT], {
        cwd: ACESTEP_DIR,
        env: {
          ...process.env,
          ACESTEP_PATH: ACESTEP_DIR,
        },
      });

      let stdout = '';
      let stderr = '';

      proc.stdout.on('data', (data) => { stdout += data.toString(); });
      proc.stderr.on('data', (data) => { stderr += data.toString(); });

      proc.on('close', (code) => {
        if (code === 0 && stdout) {
          try {
            const parsed = JSON.parse(stdout);
            resolve({ success: true, data: parsed });
          } catch {
            resolve({ success: false, error: 'Failed to parse limits result' });
          }
        } else {
          resolve({ success: false, error: stderr || 'Failed to read limits' });
        }
      });

      proc.on('error', (err) => {
        resolve({ success: false, error: err.message });
      });
    });

    if (result.success && result.data) {
      res.json(result.data);
    } else {
      res.status(500).json({ error: result.error || 'Failed to load limits' });
    }
  } catch (error) {
    console.error('Limits error:', error);
    res.status(500).json({ error: (error as Error).message });
  }
});

router.get('/debug/:taskId', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const rawResponse = getJobRawResponse(req.params.taskId);
    if (!rawResponse) {
      res.status(404).json({ error: 'Job not found or no raw response available' });
      return;
    }
    res.json({ rawResponse });
  } catch (error) {
    res.status(500).json({ error: (error as Error).message });
  }
});

// Format endpoint - uses LLM to enhance style/lyrics
// Strategy: try 8001 API first, fall back to local Python script
router.post('/format', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { caption, lyrics, bpm, duration, keyScale, timeSignature, temperature, topK, topP, lmModel, lmBackend } = req.body;

    if (!caption) {
      res.status(400).json({ error: 'Caption/style is required' });
      return;
    }

    // Attempt 1: Call 8001 API format_input endpoint
    try {
      const formatResponse = await fetchWithTimeout(`${config.acestep.apiUrl}/format_input`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': process.env.ACESTEP_API_KEY || '',
        },
        body: JSON.stringify({
          caption,
          lyrics: lyrics || '',
          bpm: bpm || 0,
          duration: duration || 0,
          key_scale: keyScale || '',
          time_signature: timeSignature || '',
          temperature: temperature,
          top_k: topK,
          top_p: topP,
        }),
      });

      if (formatResponse.ok) {
        const result = await formatResponse.json();
        res.json(result.data || result);
        return;
      }
      console.warn(`[Format] API returned ${formatResponse.status}, falling back to Python script`);
    } catch (apiError) {
      console.warn('[Format] API unavailable, falling back to Python script:', (apiError as Error).message);
    }

    // Attempt 2: Fall back to local Python script
    const { spawn } = await import('child_process');

    const ACESTEP_DIR = process.env.ACESTEP_PATH || path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../../../ACE-Step-1.5');
    const __filename = fileURLToPath(import.meta.url);
    const __dirname = path.dirname(__filename);
    const SCRIPTS_DIR = path.join(__dirname, '../../scripts');
    const FORMAT_SCRIPT = path.join(SCRIPTS_DIR, 'format_sample.py');
    const pythonPath = resolvePythonPath(ACESTEP_DIR);

    const args = [
      FORMAT_SCRIPT,
      '--caption', caption,
      '--json',
    ];

    if (lyrics) args.push('--lyrics', lyrics);
    if (bpm && bpm > 0) args.push('--bpm', String(bpm));
    if (duration && duration > 0) args.push('--duration', String(duration));
    if (keyScale) args.push('--key-scale', keyScale);
    if (timeSignature) args.push('--time-signature', timeSignature);
    if (temperature !== undefined) args.push('--temperature', String(temperature));
    if (topK && topK > 0) args.push('--top-k', String(topK));
    if (topP !== undefined) args.push('--top-p', String(topP));
    if (lmModel) args.push('--lm-model', lmModel);
    if (lmBackend) args.push('--lm-backend', lmBackend);

    const result = await new Promise<{ success: boolean; data?: any; error?: string }>((resolve) => {
      const proc = spawn(pythonPath, args, {
        cwd: ACESTEP_DIR,
        env: {
          ...process.env,
          ACESTEP_PATH: ACESTEP_DIR,
        },
      });

      let stdout = '';
      let stderr = '';

      proc.stdout.on('data', (data) => { stdout += data.toString(); });
      proc.stderr.on('data', (data) => { stderr += data.toString(); });

      proc.on('close', (code) => {
        if (code === 0 && stdout) {
          const lines = stdout.trim().split('\n');
          let jsonStr = '';
          for (let i = lines.length - 1; i >= 0; i--) {
            if (lines[i].startsWith('{')) { jsonStr = lines[i]; break; }
          }
          try {
            const parsed = JSON.parse(jsonStr || stdout);
            resolve({ success: true, data: parsed });
          } catch {
            console.error('[Format] Failed to parse stdout:', stdout.slice(0, 500));
            resolve({ success: false, error: 'Failed to parse format result' });
          }
        } else {
          console.error(`[Format] Process exited with code ${code}`);
          if (stdout) console.error('[Format] stdout:', stdout.slice(0, 1000));
          if (stderr) console.error('[Format] stderr:', stderr.slice(0, 1000));
          resolve({ success: false, error: stderr || stdout || `Format process exited with code ${code}` });
        }
      });

      proc.on('error', (err) => {
        console.error('[Format] Spawn error:', err.message);
        resolve({ success: false, error: err.message });
      });
    });

    if (result.success && result.data) {
      res.json(result.data);
    } else {
      console.error('[Format] Python error:', result.error);
      res.status(500).json({ success: false, error: result.error });
    }
  } catch (error) {
    console.error('[Format] Route error:', error);
    res.status(500).json({ error: (error as Error).message });
  }
});

export default router;
