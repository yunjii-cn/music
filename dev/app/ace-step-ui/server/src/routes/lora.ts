import { Router, Response } from 'express';
import { authMiddleware, AuthenticatedRequest } from '../middleware/auth.js';
import { config } from '../config/index.js';

const router = Router();
const ACESTEP_API_URL = config.acestep.apiUrl;
const ACESTEP_API_KEY = process.env.ACESTEP_API_KEY || '';

interface ProxyResult { status: number; data: any; }

async function proxyToAceStep(endpoint: string, method: string, data?: any, timeoutMs = 30000): Promise<ProxyResult> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (ACESTEP_API_KEY) {
    headers['x-api-key'] = ACESTEP_API_KEY;
    headers['Authorization'] = `Bearer ${ACESTEP_API_KEY}`;
  }
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  const options: RequestInit = { method, headers, signal: controller.signal };
  if (data && (method === 'POST' || method === 'PUT')) options.body = JSON.stringify(data);

  try {
    const response = await fetch(`${ACESTEP_API_URL}${endpoint}`, options);
    clearTimeout(timer);
    const result = await response.json().catch(() => ({ error: 'Request failed' }));

    let unwrapped = result;
    if (result?.data !== undefined) unwrapped = result.data;

    if (!response.ok) {
      const detail = result?.detail;
      const detailMsg = typeof detail === 'string' ? detail : undefined;
      const errorMsg = result?.error || result?.message || detailMsg || 'Request failed';
      console.error(`[LoRA proxy] ${endpoint} → ${response.status}: ${errorMsg}`);
      return { status: response.status, data: { error: errorMsg } };
    }

    if (unwrapped?.code && unwrapped.code !== 200) {
      const errorMsg = unwrapped.error || unwrapped.message || 'Request failed';
      return { status: 400, data: { error: errorMsg } };
    }

    return { status: 200, data: unwrapped };
  } catch (e: any) {
    clearTimeout(timer);
    if (e.name === 'AbortError') {
      return { status: 504, data: { error: 'AceStep API request timed out' } };
    }
    return { status: 503, data: { error: e.message || 'AceStep API unavailable' } };
  }
}

function handleProxy(res: Response, result: ProxyResult, fallbackMsg: string) {
  if (result.status !== 200) { res.status(result.status).json(result.data); return; }
  res.json(result.data || { message: fallbackMsg });
}

router.post('/load', authMiddleware, async (req, res) => {
  try { handleProxy(res, await proxyToAceStep('/v1/lora/load', 'POST', req.body), 'LoRA loaded'); }
  catch (e: any) { res.status(503).json({ error: e.message }); }
});

router.post('/unload', authMiddleware, async (_req, res) => {
  try { handleProxy(res, await proxyToAceStep('/v1/lora/unload', 'POST'), 'LoRA unloaded'); }
  catch (e: any) { res.status(503).json({ error: e.message }); }
});

router.post('/toggle', authMiddleware, async (req, res) => {
  try { handleProxy(res, await proxyToAceStep('/v1/lora/toggle', 'POST', req.body), ''); }
  catch (e: any) { res.status(503).json({ error: e.message }); }
});

router.post('/scale', authMiddleware, async (req, res) => {
  try { handleProxy(res, await proxyToAceStep('/v1/lora/scale', 'POST', req.body), ''); }
  catch (e: any) { res.status(503).json({ error: e.message }); }
});

router.get('/status', async (_req, res) => {
  try { handleProxy(res, await proxyToAceStep('/api/lora/status', 'GET'), ''); }
  catch (e: any) { res.status(503).json({ error: e.message }); }
});

router.get('/discover', async (_req, res) => {
  try {
    const result = await proxyToAceStep('/api/lora/discover', 'GET');
    if (result.status !== 200) { res.status(result.status).json(result.data); return; }
    res.json(result.data);
  } catch (e: any) { res.status(503).json({ error: e.message }); }
});

export default router;
