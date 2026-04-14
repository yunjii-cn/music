import { Router, Response } from 'express';
import { authMiddleware, AuthenticatedRequest } from '../middleware/auth.js';
import { config } from '../config/index.js';

const router = Router();

const ACESTEP_API_URL = config.acestep.apiUrl;
const ACESTEP_API_KEY = process.env.ACESTEP_API_KEY || '';

async function proxyToAceStep(endpoint: string, method: string, data?: any) {
  try {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (ACESTEP_API_KEY) {
      headers['x-api-key'] = ACESTEP_API_KEY;
      headers['Authorization'] = `Bearer ${ACESTEP_API_KEY}`;
    }

    const options: RequestInit = {
      method,
      headers,
    };

    if (data && (method === 'POST' || method === 'PUT')) {
      options.body = JSON.stringify(data);
    }

    const response = await fetch(`${ACESTEP_API_URL}${endpoint}`, options);

    if (!response.ok) {
      const errorData: any = await response.json().catch(() => ({ error: 'Request failed' }));
      const detail = errorData?.detail;
      const detailMsg = typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: any) => d?.msg || JSON.stringify(d)).join('; ')
          : undefined;
      throw new Error(errorData?.error || errorData?.message || detailMsg || 'Request failed');
    }

    const result = await response.json();

    if (result && typeof result === 'object') {
      if ('code' in result && result.code && result.code !== 200) {
        throw new Error(result.error || result.message || 'Request failed');
      }
      if ('data' in result) {
        return result.data;
      }
    }
    return result;
  } catch (error: any) {
    throw new Error(error.message || 'Request failed');
  }
}

// Dataset Builder Routes
router.post('/dataset/scan', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const result = await proxyToAceStep('/v1/dataset/scan', 'POST', req.body);
    res.json(result);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.post('/dataset/load', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    console.log('[Training] Load dataset request body:', JSON.stringify(req.body));
    const result = await proxyToAceStep('/v1/dataset/load', 'POST', req.body);
    console.log('[Training] Load dataset response:', JSON.stringify(result));
    res.json(result);
  } catch (error: any) {
    console.error('[Training] Load dataset error:', error.message);
    res.status(500).json({ error: error.message });
  }
});

router.post('/dataset/auto-label', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const result = await proxyToAceStep('/v1/dataset/auto_label', 'POST', req.body);
    res.json(result);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.post('/dataset/auto-label-async', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const result = await proxyToAceStep('/v1/dataset/auto_label_async', 'POST', req.body);
    res.json(result);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.get('/dataset/auto-label-status', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const result = await proxyToAceStep('/v1/dataset/auto_label_status', 'GET');
    res.json(result);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.get('/dataset/auto-label-status/:taskId', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const result = await proxyToAceStep(`/v1/dataset/auto_label_status/${req.params.taskId}`, 'GET');
    res.json(result);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.post('/dataset/transcribe', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const result = await proxyToAceStep('/v1/dataset/transcribe', 'POST', req.body);
    res.json(result);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.get('/dataset/transcribe-status', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const result = await proxyToAceStep('/v1/dataset/transcribe_status', 'GET');
    res.json(result);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.post('/dataset/save', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const result = await proxyToAceStep('/v1/dataset/save', 'POST', req.body);
    res.json(result);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.post('/dataset/preprocess', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const result = await proxyToAceStep('/v1/dataset/preprocess', 'POST', req.body);
    res.json(result);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.post('/dataset/preprocess-async', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const result = await proxyToAceStep('/v1/dataset/preprocess_async', 'POST', req.body);
    res.json(result);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.get('/dataset/preprocess-status', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const result = await proxyToAceStep('/v1/dataset/preprocess_status', 'GET');
    res.json(result);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.get('/dataset/preprocess-status/:taskId', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const result = await proxyToAceStep(`/v1/dataset/preprocess_status/${req.params.taskId}`, 'GET');
    res.json(result);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.get('/dataset/samples', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const result = await proxyToAceStep('/v1/dataset/samples', 'GET');
    res.json(result);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.get('/dataset/sample/:index', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const result = await proxyToAceStep(`/v1/dataset/sample/${req.params.index}`, 'GET');
    res.json(result);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.put('/dataset/sample/:index', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    console.log('PUT /dataset/sample/:index - Request body:', JSON.stringify(req.body, null, 2));
    const result = await proxyToAceStep(`/v1/dataset/sample/${req.params.index}`, 'PUT', req.body);
    res.json(result);
  } catch (error: any) {
    console.error('PUT /dataset/sample/:index - Error:', error.message);
    // Return 422 status if validation error
    if (error.message.includes('validation') || error.message.includes('422')) {
      res.status(422).json({ error: error.message, body: req.body });
    } else {
      res.status(500).json({ error: error.message });
    }
  }
});

// Training Routes
router.post('/load_tensor_info', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const result = await proxyToAceStep('/v1/training/load_tensor_info', 'POST', req.body);
    res.json(result);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.post('/start', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const result = await proxyToAceStep('/v1/training/start', 'POST', req.body);
    res.json(result);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.post('/start_lokr', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const result = await proxyToAceStep('/v1/training/start_lokr', 'POST', req.body);
    res.json(result);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.post('/stop', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const result = await proxyToAceStep('/v1/training/stop', 'POST');
    res.json(result);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.get('/status', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const result = await proxyToAceStep('/v1/training/status', 'GET');
    res.json(result);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

router.post('/export', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const result = await proxyToAceStep('/v1/training/export', 'POST', req.body);
    res.json(result);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

export default router;
