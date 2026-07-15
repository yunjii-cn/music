import { Router, Request, Response } from 'express';
import jwt, { SignOptions } from 'jsonwebtoken';
import { pool } from '../db/pool.js';
import { generateUUID } from '../db/sqlite.js';
import { config } from '../config/index.js';
import { authMiddleware, AuthenticatedRequest } from '../middleware/auth.js';

const jwtOptions = { expiresIn: config.jwt.expiresIn } as SignOptions;

const router = Router();

interface SetupBody {
  username: string;
}

function issueAccessToken(payload: { id: string; username: string }): string {
  return jwt.sign(payload, config.jwt.secret, jwtOptions);
}

// Auto-login: Get the default user from database (for local single-user app)
router.get('/auto', async (_req: Request, res: Response) => {
  try {
    // Get the first user from the database (local app typically has one user)
    const result = await pool.query(
      'SELECT id, username, bio, avatar_url, banner_url, is_admin, created_at FROM users ORDER BY created_at ASC LIMIT 1'
    );

    if (result.rows.length === 0) {
      // No user exists yet - frontend should show username setup
      res.status(404).json({ error: 'No user found' });
      return;
    }

    const user = result.rows[0];

    // Generate token for the user
    const token = issueAccessToken({
      id: user.id,
      username: user.username,
    });

    res.json({
      user: {
        id: user.id,
        username: user.username,
        bio: user.bio,
        avatar_url: user.avatar_url,
        banner_url: user.banner_url,
        isAdmin: Boolean(user.is_admin),
        createdAt: user.created_at,
      },
      token,
    });
  } catch (error) {
    console.error('Auto-login error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Setup or get user by username (simplified auth for local app)
router.post('/setup', async (req: Request<object, object, SetupBody>, res: Response) => {
  try {
    const { username } = req.body;

    if (!username || typeof username !== 'string') {
      res.status(400).json({ error: 'Username is required' });
      return;
    }

    // Sanitize username
    const sanitizedUsername = username
      .trim()
      .replace(/[^a-zA-Z0-9_-]/g, '')
      .slice(0, 50);

    if (sanitizedUsername.length < 2) {
      res.status(400).json({ error: 'Username must be at least 2 characters' });
      return;
    }

    // Check if user exists
    const existingUser = await pool.query(
      'SELECT id, username, bio, avatar_url, banner_url, is_admin, created_at FROM users WHERE username = ?',
      [sanitizedUsername]
    );

    let user;

    if (existingUser.rows.length > 0) {
      // User exists, return it
      user = existingUser.rows[0];
    } else {
      // Create new user
      const userId = generateUUID();
      await pool.query(
        `INSERT INTO users (id, username, is_admin, created_at, updated_at)
         VALUES (?, ?, 0, datetime('now'), datetime('now'))`,
        [userId, sanitizedUsername]
      );

      const newUser = await pool.query(
        'SELECT id, username, bio, avatar_url, banner_url, is_admin, created_at FROM users WHERE id = ?',
        [userId]
      );
      user = newUser.rows[0];
    }

    // Generate token
    const token = issueAccessToken({
      id: user.id,
      username: user.username,
    });

    res.status(200).json({
      user: {
        id: user.id,
        username: user.username,
        bio: user.bio,
        avatar_url: user.avatar_url,
        banner_url: user.banner_url,
        isAdmin: Boolean(user.is_admin),
        createdAt: user.created_at,
      },
      token,
    });
  } catch (error) {
    console.error('Auth setup error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// UM (云集统一用户中心) 扫码登录回调
// 接收官网登录页(web/um)扫码成功后 postMessage 过来的用户信息，
// 在本地库按 social_uid 找/建用户并签发 JWT，复用现有本地 token 体系。
router.post('/um', async (req: Request, res: Response) => {
  try {
    const body = (req.body || {}) as Record<string, unknown>;
    const socialUid = body['social_uid'];
    const nickname = typeof body['nickname'] === 'string' ? body['nickname'] : '';
    const faceimg = typeof body['faceimg'] === 'string' ? body['faceimg'] : '';

    if (typeof socialUid !== 'string' || !socialUid) {
      res.status(400).json({ error: 'Missing social_uid' });
      return;
    }

    // 1) 已绑定过 UM 账号的本地用户
    const existing = await pool.query(
      'SELECT id, username, bio, avatar_url, banner_url, is_admin, created_at FROM users WHERE um_uid = ?',
      [socialUid]
    );

    let user;
    if (existing.rows.length > 0) {
      user = existing.rows[0];
      // 同步最新头像
      if (faceimg) {
        await pool.query(
          `UPDATE users SET avatar_url = ?, updated_at = datetime('now') WHERE id = ?`,
          [faceimg, user.id]
        );
      }
    } else {
      // 2) 新用户：以昵称生成唯一 username
      const base =
        nickname.trim().replace(/[^a-zA-Z0-9_一-龥-]/g, '').slice(0, 24) || 'umuser';
      let username = base;
      let n = 1;
      // eslint-disable-next-line no-constant-condition
      while (true) {
        const clash = await pool.query('SELECT id FROM users WHERE username = ?', [username]);
        if (clash.rows.length === 0) break;
        username = `${base}${n}`;
        n++;
        if (n > 9999) {
          username = `um_${socialUid.slice(-6)}`;
          break;
        }
      }
      const userId = generateUUID();
      await pool.query(
        `INSERT INTO users (id, username, avatar_url, um_uid, is_admin, created_at, updated_at)
         VALUES (?, ?, ?, ?, 0, datetime('now'), datetime('now'))`,
        [userId, username, faceimg || null, socialUid]
      );
      const newUser = await pool.query(
        'SELECT id, username, bio, avatar_url, banner_url, is_admin, created_at FROM users WHERE id = ?',
        [userId]
      );
      user = newUser.rows[0];
    }

    const token = issueAccessToken({ id: user.id, username: user.username });

    res.status(200).json({
      user: {
        id: user.id,
        username: user.username,
        bio: user.bio,
        avatar_url: user.avatar_url,
        banner_url: user.banner_url,
        isAdmin: Boolean(user.is_admin),
        createdAt: user.created_at,
      },
      token,
    });
  } catch (error) {
    console.error('UM auth error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get current user
router.get('/me', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const result = await pool.query(
      'SELECT id, username, bio, avatar_url, banner_url, is_admin, created_at FROM users WHERE id = ?',
      [req.user!.id]
    );

    if (result.rows.length === 0) {
      res.status(404).json({ error: 'User not found' });
      return;
    }

    const user = result.rows[0];
    res.json({
      user: {
        id: user.id,
        username: user.username,
        bio: user.bio,
        avatar_url: user.avatar_url,
        banner_url: user.banner_url,
        isAdmin: Boolean(user.is_admin),
        createdAt: user.created_at,
      },
    });
  } catch (error) {
    console.error('Get user error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Update username
router.patch('/username', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { username } = req.body;

    if (!username || typeof username !== 'string') {
      res.status(400).json({ error: 'Username is required' });
      return;
    }

    // Sanitize username
    const sanitizedUsername = username
      .trim()
      .replace(/[^a-zA-Z0-9_-]/g, '')
      .slice(0, 50);

    if (sanitizedUsername.length < 2) {
      res.status(400).json({ error: 'Username must be at least 2 characters' });
      return;
    }

    // Check if username is taken by another user
    const existingUser = await pool.query(
      'SELECT id FROM users WHERE username = ? AND id != ?',
      [sanitizedUsername, req.user!.id]
    );

    if (existingUser.rows.length > 0) {
      res.status(409).json({ error: 'Username is already taken' });
      return;
    }

    // Update username
    await pool.query(
      `UPDATE users SET username = ?, updated_at = datetime('now') WHERE id = ?`,
      [sanitizedUsername, req.user!.id]
    );

    // Get updated user
    const result = await pool.query(
      'SELECT id, username, bio, avatar_url, banner_url, is_admin, created_at FROM users WHERE id = ?',
      [req.user!.id]
    );

    const user = result.rows[0];

    // Issue new token with updated username
    const token = issueAccessToken({
      id: user.id,
      username: user.username,
    });

    res.json({
      user: {
        id: user.id,
        username: user.username,
        bio: user.bio,
        avatar_url: user.avatar_url,
        banner_url: user.banner_url,
        isAdmin: Boolean(user.is_admin),
        createdAt: user.created_at,
      },
      token,
    });
  } catch (error) {
    console.error('Update username error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Logout (no-op for local app, just for API compatibility)
router.post('/logout', async (_req: Request, res: Response) => {
  res.json({ success: true });
});

// Refresh token (for API compatibility - just returns current user if token valid)
router.post('/refresh', authMiddleware, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const result = await pool.query(
      'SELECT id, username, bio, avatar_url, banner_url, is_admin, created_at FROM users WHERE id = ?',
      [req.user!.id]
    );

    if (result.rows.length === 0) {
      res.status(404).json({ error: 'User not found' });
      return;
    }

    const user = result.rows[0];
    const token = issueAccessToken({
      id: user.id,
      username: user.username,
    });

    res.json({
      user: {
        id: user.id,
        username: user.username,
        bio: user.bio,
        avatar_url: user.avatar_url,
        banner_url: user.banner_url,
        isAdmin: Boolean(user.is_admin),
        createdAt: user.created_at,
      },
      token,
    });
  } catch (error) {
    console.error('Refresh token error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

export default router;
