import { Router, Response } from 'express';
import { pool } from '../db/pool.js';
import { authMiddleware, AuthenticatedRequest } from '../middleware/auth.js';
import { randomUUID } from 'crypto';

const router = Router();

function formatProject(row: Record<string, unknown>) {
  return {
    ...row,
    is_active: Boolean(row.is_active),
    auto_save_enabled: Boolean(row.auto_save_enabled),
    is_default: Boolean(row.is_default),
    params: typeof row.params === 'string' ? JSON.parse(row.params) : row.params,
  };
}

async function ensureDefaultProject(userId: string): Promise<Record<string, unknown>> {
  const existing = await pool.query(
    `SELECT id, name, description, params, is_active, is_default, auto_save_enabled, auto_save_interval, auto_save_max_count, created_at, updated_at
     FROM projects WHERE user_id = ? AND is_default = 1`,
    [userId]
  );
  if (existing.rows.length > 0) {
    return formatProject(existing.rows[0]);
  }

  const id = randomUUID();
  const result = await pool.query(
    `INSERT INTO projects (id, user_id, name, description, params, is_active, is_default, auto_save_enabled, auto_save_interval, auto_save_max_count)
     VALUES (?, ?, ?, ?, ?, 0, 1, 1, 60, 50)
     RETURNING *`,
    [id, userId, '未命名项目', null, JSON.stringify({})]
  );

  return formatProject(result.rows[0]);
}

router.get('/', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const userId = req.user!.id;

    const result = await pool.query(
      `SELECT id, name, description, params, is_active, is_default, auto_save_enabled, auto_save_interval, auto_save_max_count, created_at, updated_at
       FROM projects
       WHERE user_id = ?
       ORDER BY is_active DESC, updated_at DESC`,
      [userId]
    );

    const projects = result.rows.map(row => formatProject(row));
    const defaultProject = projects.find(p => p.is_default) || null;

    if (!defaultProject) {
      const id = randomUUID();
      const insertResult = await pool.query(
        `INSERT INTO projects (id, user_id, name, description, params, is_active, is_default, auto_save_enabled, auto_save_interval, auto_save_max_count)
         VALUES (?, ?, ?, ?, ?, 0, 1, 1, 60, 50)
         RETURNING *`,
        [id, userId, '未命名项目', null, JSON.stringify({})]
      );
      const newDefault = formatProject(insertResult.rows[0]);
      projects.push(newDefault);
      res.json({ projects, default_project: newDefault });
    } else {
      res.json({ projects, default_project: defaultProject });
    }
  } catch (error) {
    console.error('Get projects error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.get('/default', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const userId = req.user!.id;
    const defaultProject = await ensureDefaultProject(userId);
    res.json({ project: defaultProject });
  } catch (error) {
    console.error('Get default project error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.get('/:id', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const result = await pool.query(
      `SELECT id, name, description, params, is_active, is_default, auto_save_enabled, auto_save_interval, auto_save_max_count, created_at, updated_at
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

    res.json({ project: formatProject(result.rows[0]) });
  } catch (error) {
    console.error('Get project error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.post('/', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const userId = req.user!.id;
    const { name, description, params, auto_save_enabled, auto_save_interval, auto_save_max_count, from_default } = req.body;

    if (!name || !name.trim()) {
      res.status(400).json({ error: 'Project name is required' });
      return;
    }

    const id = randomUUID();

    await pool.query(
      `UPDATE projects SET is_active = 0 WHERE user_id = ? AND is_active = 1`,
      [userId]
    );

    if (from_default) {
      const defaultProject = await pool.query(
        `SELECT id FROM projects WHERE user_id = ? AND is_default = 1`,
        [userId]
      );
      if (defaultProject.rows.length > 0) {
        await pool.query(
          `UPDATE projects SET name = ?, description = ?, is_default = 0, is_active = 1, updated_at = datetime('now') WHERE id = ?`,
          [name.trim(), description?.trim() || null, defaultProject.rows[0].id]
        );

        const newDefaultId = randomUUID();
        await pool.query(
          `INSERT INTO projects (id, user_id, name, description, params, is_active, is_default, auto_save_enabled, auto_save_interval, auto_save_max_count)
           VALUES (?, ?, '未命名项目', NULL, '{}', 0, 1, 1, 60, 50)`,
          [newDefaultId, userId]
        );

        const result = await pool.query(
          `SELECT id, name, description, params, is_active, is_default, auto_save_enabled, auto_save_interval, auto_save_max_count, created_at, updated_at
           FROM projects WHERE id = ?`,
          [defaultProject.rows[0].id]
        );
        res.status(201).json({ project: formatProject(result.rows[0]) });
        return;
      }
    }

    const result = await pool.query(
      `INSERT INTO projects (id, user_id, name, description, params, is_active, is_default, auto_save_enabled, auto_save_interval, auto_save_max_count)
       VALUES (?, ?, ?, ?, ?, 1, 0, ?, ?, ?)
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

    res.status(201).json({ project: formatProject(result.rows[0]) });
  } catch (error) {
    console.error('Create project error:', error);
    res.status(500).json({ error: 'Failed to create project' });
  }
});

router.patch('/:id', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const check = await pool.query(
      'SELECT user_id, params FROM projects WHERE id = ?',
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

    const { name, description, params, auto_save_enabled, auto_save_interval, auto_save_max_count, changelog_label } = req.body;
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

      const oldParams = typeof check.rows[0].params === 'string' ? JSON.parse(check.rows[0].params) : (check.rows[0].params || {});
      const newParams = params;
      const changes: Record<string, { old: unknown; new: unknown }> = {};
      const allKeys = new Set([...Object.keys(oldParams), ...Object.keys(newParams)]);
      for (const key of allKeys) {
        const oldVal = oldParams[key];
        const newVal = newParams[key];
        if (JSON.stringify(oldVal) !== JSON.stringify(newVal)) {
          changes[key] = { old: oldVal, new: newVal };
        }
      }

      if (Object.keys(changes).length > 0) {
        const logId = randomUUID();
        const action = Object.keys(changes).length <= 3
          ? Object.keys(changes).map(k => `${k}: ${JSON.stringify(changes[k].old)} → ${JSON.stringify(changes[k].new)}`).join(', ')
          : `修改了 ${Object.keys(changes).length} 个参数`;
        await pool.query(
          `INSERT INTO project_changelogs (id, project_id, action, label, changes, snapshot_params)
           VALUES (?, ?, ?, ?, ?, ?)`,
          [
            logId,
            req.params.id,
            action,
            changelog_label || null,
            JSON.stringify(changes),
            JSON.stringify(newParams),
          ]
        );
      }
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

    res.json({ project: formatProject(result.rows[0]) });
  } catch (error) {
    console.error('Update project error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.delete('/:id', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const check = await pool.query(
      'SELECT user_id, is_default FROM projects WHERE id = ?',
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
    if (Boolean(check.rows[0].is_default)) {
      res.status(400).json({ error: 'Cannot delete default project' });
      return;
    }

    await pool.query('DELETE FROM projects WHERE id = ?', [req.params.id]);

    const userId = req.user!.id;
    const remaining = await pool.query(
      'SELECT id FROM projects WHERE user_id = ? LIMIT 1',
      [userId]
    );
    if (remaining.rows.length === 0) {
      await ensureDefaultProject(userId);
    }

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
    await pool.query("UPDATE projects SET is_active = 1, updated_at = datetime('now') WHERE id = ?", [req.params.id]);

    const result = await pool.query(
      `SELECT id, name, description, params, is_active, is_default, auto_save_enabled, auto_save_interval, auto_save_max_count, created_at, updated_at
       FROM projects WHERE id = ?`,
      [req.params.id]
    );

    res.json({ project: formatProject(result.rows[0]) });
  } catch (error) {
    console.error('Activate project error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.post('/:id/rename', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const check = await pool.query(
      'SELECT user_id, is_default FROM projects WHERE id = ?',
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

    const { name } = req.body;
    if (!name || !name.trim()) {
      res.status(400).json({ error: 'Project name is required' });
      return;
    }

    await pool.query(
      "UPDATE projects SET name = ?, is_default = 0, updated_at = datetime('now') WHERE id = ?",
      [name.trim(), req.params.id]
    );

    const existingDefault = await pool.query(
      'SELECT id FROM projects WHERE user_id = ? AND is_default = 1',
      [req.user!.id]
    );
    if (existingDefault.rows.length === 0) {
      const newDefaultId = randomUUID();
      await pool.query(
        `INSERT INTO projects (id, user_id, name, description, params, is_active, is_default, auto_save_enabled, auto_save_interval, auto_save_max_count)
         VALUES (?, ?, '未命名项目', NULL, '{}', 0, 1, 1, 60, 50)`,
        [newDefaultId, req.user!.id]
      );
    }

    const result = await pool.query(
      `SELECT id, name, description, params, is_active, is_default, auto_save_enabled, auto_save_interval, auto_save_max_count, created_at, updated_at
       FROM projects WHERE id = ?`,
      [req.params.id]
    );

    res.json({ project: formatProject(result.rows[0]) });
  } catch (error) {
    console.error('Rename project error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.get('/:id/changelogs', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
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

    const limit = Math.min(parseInt(req.query.limit as string) || 100, 500);
    const offset = parseInt(req.query.offset as string) || 0;

    const result = await pool.query(
      `SELECT id, project_id, action, label, changes, snapshot_params, created_at
       FROM project_changelogs
       WHERE project_id = ?
       ORDER BY created_at DESC
       LIMIT ? OFFSET ?`,
      [req.params.id, limit, offset]
    );

    const countResult = await pool.query(
      'SELECT COUNT(*) as total FROM project_changelogs WHERE project_id = ?',
      [req.params.id]
    );

    const changelogs = result.rows.map(row => ({
      ...row,
      changes: typeof row.changes === 'string' ? JSON.parse(row.changes) : row.changes,
      snapshot_params: typeof row.snapshot_params === 'string' ? JSON.parse(row.snapshot_params) : row.snapshot_params,
    }));

    res.json({ changelogs, total: countResult.rows[0]?.total || 0 });
  } catch (error) {
    console.error('Get changelogs error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.post('/:id/changelogs', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
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

    const { action, label, changes, snapshot_params } = req.body;
    if (!action || !changes || !snapshot_params) {
      res.status(400).json({ error: 'action, changes, and snapshot_params are required' });
      return;
    }

    const id = randomUUID();
    const result = await pool.query(
      `INSERT INTO project_changelogs (id, project_id, action, label, changes, snapshot_params)
       VALUES (?, ?, ?, ?, ?, ?)
       RETURNING *`,
      [
        id,
        req.params.id,
        action,
        label?.trim() || null,
        JSON.stringify(changes),
        JSON.stringify(snapshot_params),
      ]
    );

    const changelog = {
      ...result.rows[0],
      changes: typeof result.rows[0].changes === 'string' ? JSON.parse(result.rows[0].changes) : result.rows[0].changes,
      snapshot_params: typeof result.rows[0].snapshot_params === 'string' ? JSON.parse(result.rows[0].snapshot_params) : result.rows[0].snapshot_params,
    };

    res.status(201).json({ changelog });
  } catch (error) {
    console.error('Create changelog error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.post('/:id/undo', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const check = await pool.query(
      'SELECT user_id, params FROM projects WHERE id = ?',
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

    const lastLog = await pool.query(
      `SELECT id, action, changes, snapshot_params, created_at
       FROM project_changelogs
       WHERE project_id = ?
       ORDER BY created_at DESC
       LIMIT 1`,
      [req.params.id]
    );

    if (lastLog.rows.length === 0) {
      res.status(400).json({ error: 'No changes to undo' });
      return;
    }

    const changes = typeof lastLog.rows[0].changes === 'string' ? JSON.parse(lastLog.rows[0].changes) : lastLog.rows[0].changes;
    const currentParams = typeof check.rows[0].params === 'string' ? JSON.parse(check.rows[0].params) : (check.rows[0].params || {});

    const restoredParams = { ...currentParams };
    for (const [key, change] of Object.entries(changes)) {
      const c = change as { old: unknown; new: unknown };
      if (c.old === undefined || c.old === null) {
        delete restoredParams[key];
      } else {
        restoredParams[key] = c.old;
      }
    }

    await pool.query(
      "UPDATE projects SET params = ?, updated_at = datetime('now') WHERE id = ?",
      [JSON.stringify(restoredParams), req.params.id]
    );

    await pool.query(
      'DELETE FROM project_changelogs WHERE id = ?',
      [lastLog.rows[0].id]
    );

    const projectResult = await pool.query(
      `SELECT id, name, description, params, is_active, is_default, auto_save_enabled, auto_save_interval, auto_save_max_count, created_at, updated_at
       FROM projects WHERE id = ?`,
      [req.params.id]
    );

    res.json({
      project: formatProject(projectResult.rows[0]),
      undone_changes: changes,
      undone_action: lastLog.rows[0].action,
    });
  } catch (error) {
    console.error('Undo error:', error);
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
      'SELECT user_id, params FROM projects WHERE id = ?',
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

    const oldParams = typeof projectCheck.rows[0].params === 'string' ? JSON.parse(projectCheck.rows[0].params) : (projectCheck.rows[0].params || {});
    const snapshotParams = typeof snapshotResult.rows[0].params === 'string' ? JSON.parse(snapshotResult.rows[0].params) : snapshotResult.rows[0].params;

    const changes: Record<string, { old: unknown; new: unknown }> = {};
    const allKeys = new Set([...Object.keys(oldParams), ...Object.keys(snapshotParams)]);
    for (const key of allKeys) {
      if (JSON.stringify(oldParams[key]) !== JSON.stringify(snapshotParams[key])) {
        changes[key] = { old: oldParams[key], new: snapshotParams[key] };
      }
    }

    if (Object.keys(changes).length > 0) {
      const logId = randomUUID();
      const action = `恢复快照: ${snapshotResult.rows[0].label || snapshotResult.rows[0].id.slice(0, 8)}`;
      await pool.query(
        `INSERT INTO project_changelogs (id, project_id, action, label, changes, snapshot_params)
         VALUES (?, ?, ?, ?, ?, ?)`,
        [logId, req.params.id, action, 'restore', JSON.stringify(changes), JSON.stringify(snapshotParams)]
      );
    }

    await pool.query(
      "UPDATE projects SET params = ?, updated_at = datetime('now') WHERE id = ?",
      [typeof snapshotResult.rows[0].params === 'string' ? snapshotResult.rows[0].params : JSON.stringify(snapshotParams), req.params.id]
    );

    const projectResult = await pool.query(
      `SELECT id, name, description, params, is_active, is_default, auto_save_enabled, auto_save_interval, auto_save_max_count, created_at, updated_at
       FROM projects WHERE id = ?`,
      [req.params.id]
    );

    res.json({ project: formatProject(projectResult.rows[0]) });
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
