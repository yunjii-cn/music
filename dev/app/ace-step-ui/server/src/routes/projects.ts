import { Router, Response } from 'express';
import { pool } from '../db/pool.js';
import { authMiddleware, AuthenticatedRequest } from '../middleware/auth.js';
import { randomUUID } from 'crypto';

const router = Router();

router.get('/', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const userId = req.user!.id;
    const result = await pool.query(
      `SELECT id, name, description, params, is_active, auto_save_enabled, auto_save_interval, auto_save_max_count, created_at, updated_at
       FROM projects
       WHERE user_id = ?
       ORDER BY is_active DESC, updated_at DESC`,
      [userId]
    );

    const projects = result.rows.map(row => ({
      ...row,
      is_active: Boolean(row.is_active),
      auto_save_enabled: Boolean(row.auto_save_enabled),
      params: typeof row.params === 'string' ? JSON.parse(row.params) : row.params,
    }));

    res.json({ projects });
  } catch (error) {
    console.error('Get projects error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.get('/:id', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const result = await pool.query(
      `SELECT id, name, description, params, is_active, auto_save_enabled, auto_save_interval, auto_save_max_count, created_at, updated_at
       FROM projects WHERE id = ?`,
      [req.params.id]
    );
    if (result.rows.length === 0) {
      res.status(404).json({ error: 'Project not found' });
      return;
    }
    if (result.rows[0].user_id !== req.user!.id) {
      res.status(403).json({ error: 'Access denied' });
      return;
    }

    const project = {
      ...result.rows[0],
      is_active: Boolean(result.rows[0].is_active),
      auto_save_enabled: Boolean(result.rows[0].auto_save_enabled),
      params: typeof result.rows[0].params === 'string' ? JSON.parse(result.rows[0].params) : result.rows[0].params,
    };

    res.json({ project });
  } catch (error) {
    console.error('Get project error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.post('/', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const userId = req.user!.id;
    const { name, description, params, auto_save_enabled, auto_save_interval, auto_save_max_count } = req.body;

    if (!name || !name.trim()) {
      res.status(400).json({ error: 'Project name is required' });
      return;
    }

    const id = randomUUID();

    await pool.query(
      `UPDATE projects SET is_active = 0 WHERE user_id = ? AND is_active = 1`,
      [userId]
    );

    const result = await pool.query(
      `INSERT INTO projects (id, user_id, name, description, params, is_active, auto_save_enabled, auto_save_interval, auto_save_max_count)
       VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?)
       RETURNING *`,
      [
        id,
        userId,
        name.trim(),
        description?.trim() || null,
        JSON.stringify(params || {}),
        auto_save_enabled !== undefined ? (auto_save_enabled ? 1 : 0) : 1,
        auto_save_interval || 60,
        auto_save_max_count || 50,
      ]
    );

    const project = result.rows[0];
    res.status(201).json({
      project: {
        ...project,
        is_active: Boolean(project.is_active),
        auto_save_enabled: Boolean(project.auto_save_enabled),
        params: typeof project.params === 'string' ? JSON.parse(project.params) : project.params,
      },
    });
  } catch (error) {
    console.error('Create project error:', error);
    res.status(500).json({ error: 'Failed to create project' });
  }
});

router.patch('/:id', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const check = await pool.query(
      'SELECT user_id FROM projects WHERE id = ?',
      [req.params.id]
    );
    if (check.rows.length === 0) {
      res.status(404).json({ error: 'Project not found' });
      return;
    }
    if (check.rows[0].user_id !== req.user!.id) {
      res.status(403).json({ error: 'Access denied' });
      return;
    }

    const { name, description, params, auto_save_enabled, auto_save_interval, auto_save_max_count } = req.body;
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
    if (params !== undefined) {
      updates.push('params = ?');
      values.push(JSON.stringify(params));
    }
    if (auto_save_enabled !== undefined) {
      updates.push('auto_save_enabled = ?');
      values.push(auto_save_enabled ? 1 : 0);
    }
    if (auto_save_interval !== undefined) {
      updates.push('auto_save_interval = ?');
      values.push(auto_save_interval);
    }
    if (auto_save_max_count !== undefined) {
      updates.push('auto_save_max_count = ?');
      values.push(auto_save_max_count);
    }

    if (updates.length === 0) {
      res.status(400).json({ error: 'No fields to update' });
      return;
    }

    updates.push("updated_at = datetime('now')");
    values.push(req.params.id);

    const result = await pool.query(
      `UPDATE projects SET ${updates.join(', ')} WHERE id = ? RETURNING *`,
      values
    );

    const project = result.rows[0];
    res.json({
      project: {
        ...project,
        is_active: Boolean(project.is_active),
        auto_save_enabled: Boolean(project.auto_save_enabled),
        params: typeof project.params === 'string' ? JSON.parse(project.params) : project.params,
      },
    });
  } catch (error) {
    console.error('Update project error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.delete('/:id', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const check = await pool.query(
      'SELECT user_id FROM projects WHERE id = ?',
      [req.params.id]
    );
    if (check.rows.length === 0) {
      res.status(404).json({ error: 'Project not found' });
      return;
    }
    if (check.rows[0].user_id !== req.user!.id) {
      res.status(403).json({ error: 'Access denied' });
      return;
    }

    await pool.query('DELETE FROM projects WHERE id = ?', [req.params.id]);
    res.json({ success: true });
  } catch (error) {
    console.error('Delete project error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.post('/:id/activate', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const check = await pool.query(
      'SELECT user_id FROM projects WHERE id = ?',
      [req.params.id]
    );
    if (check.rows.length === 0) {
      res.status(404).json({ error: 'Project not found' });
      return;
    }
    if (check.rows[0].user_id !== req.user!.id) {
      res.status(403).json({ error: 'Access denied' });
      return;
    }

    const userId = req.user!.id;
    await pool.query('UPDATE projects SET is_active = 0 WHERE user_id = ? AND is_active = 1', [userId]);
    await pool.query('UPDATE projects SET is_active = 1, updated_at = datetime(\'now\') WHERE id = ?', [req.params.id]);

    const result = await pool.query(
      `SELECT id, name, description, params, is_active, auto_save_enabled, auto_save_interval, auto_save_max_count, created_at, updated_at
       FROM projects WHERE id = ?`,
      [req.params.id]
    );

    const project = {
      ...result.rows[0],
      is_active: Boolean(result.rows[0].is_active),
      auto_save_enabled: Boolean(result.rows[0].auto_save_enabled),
      params: typeof result.rows[0].params === 'string' ? JSON.parse(result.rows[0].params) : result.rows[0].params,
    };

    res.json({ project });
  } catch (error) {
    console.error('Activate project error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.get('/:id/snapshots', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const check = await pool.query(
      'SELECT user_id FROM projects WHERE id = ?',
      [req.params.id]
    );
    if (check.rows.length === 0) {
      res.status(404).json({ error: 'Project not found' });
      return;
    }
    if (check.rows[0].user_id !== req.user!.id) {
      res.status(403).json({ error: 'Access denied' });
      return;
    }

    const result = await pool.query(
      `SELECT id, project_id, label, params, is_auto, created_at
       FROM project_snapshots
       WHERE project_id = ?
       ORDER BY created_at DESC
       LIMIT 100`,
      [req.params.id]
    );

    const snapshots = result.rows.map(row => ({
      ...row,
      is_auto: Boolean(row.is_auto),
      params: typeof row.params === 'string' ? JSON.parse(row.params) : row.params,
    }));

    res.json({ snapshots });
  } catch (error) {
    console.error('Get snapshots error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.post('/:id/snapshots', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const check = await pool.query(
      'SELECT user_id, auto_save_max_count FROM projects WHERE id = ?',
      [req.params.id]
    );
    if (check.rows.length === 0) {
      res.status(404).json({ error: 'Project not found' });
      return;
    }
    if (check.rows[0].user_id !== req.user!.id) {
      res.status(403).json({ error: 'Access denied' });
      return;
    }

    const { label, params, is_auto } = req.body;
    if (!params || typeof params !== 'object') {
      res.status(400).json({ error: 'Snapshot params are required' });
      return;
    }

    const id = randomUUID();
    const maxCount = check.rows[0].auto_save_max_count || 50;

    if (is_auto) {
      const autoCount = await pool.query(
        'SELECT COUNT(*) as cnt FROM project_snapshots WHERE project_id = ? AND is_auto = 1',
        [req.params.id]
      );
      const count = autoCount.rows[0]?.cnt || 0;
      if (count >= maxCount) {
        const oldest = await pool.query(
          `SELECT id FROM project_snapshots WHERE project_id = ? AND is_auto = 1 ORDER BY created_at ASC LIMIT ?`,
          [req.params.id, count - maxCount + 1]
        );
        for (const row of oldest.rows) {
          await pool.query('DELETE FROM project_snapshots WHERE id = ?', [row.id]);
        }
      }
    }

    const result = await pool.query(
      `INSERT INTO project_snapshots (id, project_id, label, params, is_auto)
       VALUES (?, ?, ?, ?, ?)
       RETURNING *`,
      [id, req.params.id, label?.trim() || null, JSON.stringify(params), is_auto ? 1 : 0]
    );

    const snapshot = {
      ...result.rows[0],
      is_auto: Boolean(result.rows[0].is_auto),
      params: typeof result.rows[0].params === 'string' ? JSON.parse(result.rows[0].params) : result.rows[0].params,
    };

    res.status(201).json({ snapshot });
  } catch (error) {
    console.error('Create snapshot error:', error);
    res.status(500).json({ error: 'Failed to create snapshot' });
  }
});

router.post('/:id/snapshots/:snapshotId/restore', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const projectCheck = await pool.query(
      'SELECT user_id FROM projects WHERE id = ?',
      [req.params.id]
    );
    if (projectCheck.rows.length === 0) {
      res.status(404).json({ error: 'Project not found' });
      return;
    }
    if (projectCheck.rows[0].user_id !== req.user!.id) {
      res.status(403).json({ error: 'Access denied' });
      return;
    }

    const snapshotResult = await pool.query(
      'SELECT id, project_id, label, params, is_auto, created_at FROM project_snapshots WHERE id = ?',
      [req.params.snapshotId]
    );
    if (snapshotResult.rows.length === 0) {
      res.status(404).json({ error: 'Snapshot not found' });
      return;
    }
    if (snapshotResult.rows[0].project_id !== req.params.id) {
      res.status(400).json({ error: 'Snapshot does not belong to this project' });
      return;
    }

    const snapshotParams = snapshotResult.rows[0].params;
    await pool.query(
      "UPDATE projects SET params = ?, updated_at = datetime('now') WHERE id = ?",
      [typeof snapshotParams === 'string' ? snapshotParams : JSON.stringify(snapshotParams), req.params.id]
    );

    const projectResult = await pool.query(
      `SELECT id, name, description, params, is_active, auto_save_enabled, auto_save_interval, auto_save_max_count, created_at, updated_at
       FROM projects WHERE id = ?`,
      [req.params.id]
    );

    const project = {
      ...projectResult.rows[0],
      is_active: Boolean(projectResult.rows[0].is_active),
      auto_save_enabled: Boolean(projectResult.rows[0].auto_save_enabled),
      params: typeof projectResult.rows[0].params === 'string' ? JSON.parse(projectResult.rows[0].params) : projectResult.rows[0].params,
    };

    res.json({ project });
  } catch (error) {
    console.error('Restore snapshot error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.delete('/:id/snapshots/:snapshotId', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const projectCheck = await pool.query(
      'SELECT user_id FROM projects WHERE id = ?',
      [req.params.id]
    );
    if (projectCheck.rows.length === 0) {
      res.status(404).json({ error: 'Project not found' });
      return;
    }
    if (projectCheck.rows[0].user_id !== req.user!.id) {
      res.status(403).json({ error: 'Access denied' });
      return;
    }

    await pool.query('DELETE FROM project_snapshots WHERE id = ? AND project_id = ?', [req.params.snapshotId, req.params.id]);
    res.json({ success: true });
  } catch (error) {
    console.error('Delete snapshot error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

export default router;
