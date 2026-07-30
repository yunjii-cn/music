import { Router, Request, Response } from 'express';
import { promises as fs } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// Persist the frontend UI state (lyrics, settings, etc.) to a file on disk
// so it survives browser changes / cache clears. The frontend mirrors its
// localStorage ("ace-*", "acestep_*", "theme", "volume" keys) here in real time.
const router = Router();
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DATA_DIR = path.join(__dirname, '../../data');
const STATE_FILE = path.join(DATA_DIR, 'ui-state.json');

async function readState(): Promise<Record<string, string>> {
  try {
    const raw = await fs.readFile(STATE_FILE, 'utf-8');
    const parsed = JSON.parse(raw || '{}');
    return parsed && typeof parsed === 'object' ? parsed : {};
  } catch {
    return {};
  }
}

// GET current persisted UI state
router.get('/', async (_req: Request, res: Response) => {
  const data = await readState();
  res.json({ success: true, data });
});

// PUT (replace) the full UI state
router.put('/', async (req: Request, res: Response) => {
  try {
    const body = req.body;
    const data: Record<string, string> =
      body && typeof body === 'object' && !Array.isArray(body) ? body : {};
    await fs.mkdir(DATA_DIR, { recursive: true });
    await fs.writeFile(STATE_FILE, JSON.stringify(data, null, 2), 'utf-8');
    res.json({ success: true });
  } catch (e) {
    res.status(500).json({ success: false, error: String(e) });
  }
});

export default router;
