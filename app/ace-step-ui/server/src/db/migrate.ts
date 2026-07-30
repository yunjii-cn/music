import { db } from './pool.js';

const migrations = `
-- Users table (simplified - no credits, no stripe, no tiers)
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  bio TEXT,
  avatar_url TEXT,
  banner_url TEXT,
  is_admin INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

-- Songs table
CREATE TABLE IF NOT EXISTS songs (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  lyrics TEXT,
  style TEXT,
  caption TEXT,
  cover_url TEXT,
  audio_url TEXT,
  duration INTEGER,
  bpm INTEGER,
  key_scale TEXT,
  time_signature TEXT,
  tags TEXT DEFAULT '[]',
  is_public INTEGER DEFAULT 0,
  is_featured INTEGER DEFAULT 0,
  like_count INTEGER DEFAULT 0,
  view_count INTEGER DEFAULT 0,
  has_video INTEGER DEFAULT 0,
  video_url TEXT,
  model TEXT,
  generation_params TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

-- Generation jobs table (simplified - no credit_reserved)
CREATE TABLE IF NOT EXISTS generation_jobs (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  acestep_task_id TEXT,
  status TEXT DEFAULT 'pending',
  params TEXT,
  result TEXT,
  error TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

-- Playlists table
CREATE TABLE IF NOT EXISTS playlists (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  cover_url TEXT,
  is_public INTEGER DEFAULT 1,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

-- Playlist songs junction table
CREATE TABLE IF NOT EXISTS playlist_songs (
  playlist_id TEXT NOT NULL REFERENCES playlists(id) ON DELETE CASCADE,
  song_id TEXT NOT NULL REFERENCES songs(id) ON DELETE CASCADE,
  position INTEGER NOT NULL DEFAULT 0,
  added_at TEXT DEFAULT (datetime('now')),
  PRIMARY KEY (playlist_id, song_id)
);

-- Liked songs table
CREATE TABLE IF NOT EXISTS liked_songs (
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  song_id TEXT NOT NULL REFERENCES songs(id) ON DELETE CASCADE,
  liked_at TEXT DEFAULT (datetime('now')),
  PRIMARY KEY (user_id, song_id)
);

-- Comments table
CREATE TABLE IF NOT EXISTS comments (
  id TEXT PRIMARY KEY,
  song_id TEXT NOT NULL REFERENCES songs(id) ON DELETE CASCADE,
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

-- Followers table
CREATE TABLE IF NOT EXISTS followers (
  follower_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  following_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at TEXT DEFAULT (datetime('now')),
  PRIMARY KEY (follower_id, following_id),
  CHECK (follower_id != following_id)
);

-- Reference tracks (uploaded audio for use as references)
CREATE TABLE IF NOT EXISTS reference_tracks (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  filename TEXT NOT NULL,
  storage_key TEXT NOT NULL,
  duration INTEGER,
  file_size_bytes INTEGER,
  tags TEXT DEFAULT '[]',
  created_at TEXT DEFAULT (datetime('now'))
);

-- Contact submissions table
CREATE TABLE IF NOT EXISTS contact_submissions (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  subject TEXT NOT NULL,
  message TEXT NOT NULL,
  category TEXT DEFAULT 'general',
  is_read INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now'))
);

-- Audio files table (for tracking uploaded/generated audio with storage metadata)
CREATE TABLE IF NOT EXISTS audio_files (
  id TEXT PRIMARY KEY,
  song_id TEXT NOT NULL REFERENCES songs(id) ON DELETE CASCADE,
  storage_key TEXT NOT NULL,
  storage_provider TEXT DEFAULT 'local',
  file_size_bytes INTEGER,
  expires_at TEXT,
  deleted_at TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_songs_user_id ON songs(user_id);
CREATE INDEX IF NOT EXISTS idx_songs_created_at ON songs(created_at);
CREATE INDEX IF NOT EXISTS idx_songs_is_public ON songs(is_public);
CREATE INDEX IF NOT EXISTS idx_songs_is_featured ON songs(is_featured);
CREATE INDEX IF NOT EXISTS idx_generation_jobs_user_id ON generation_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_generation_jobs_status ON generation_jobs(status);
CREATE INDEX IF NOT EXISTS idx_generation_jobs_created_at ON generation_jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_playlists_user_id ON playlists(user_id);
CREATE INDEX IF NOT EXISTS idx_comments_song_id ON comments(song_id);
CREATE INDEX IF NOT EXISTS idx_comments_created_at ON comments(created_at);
CREATE INDEX IF NOT EXISTS idx_followers_follower ON followers(follower_id);
CREATE INDEX IF NOT EXISTS idx_followers_following ON followers(following_id);
CREATE INDEX IF NOT EXISTS idx_reference_tracks_user_id ON reference_tracks(user_id);
CREATE INDEX IF NOT EXISTS idx_reference_tracks_created_at ON reference_tracks(created_at);
CREATE INDEX IF NOT EXISTS idx_audio_files_song_id ON audio_files(song_id);
CREATE INDEX IF NOT EXISTS idx_audio_files_deleted_at ON audio_files(deleted_at);
CREATE INDEX IF NOT EXISTS idx_audio_files_expires_at ON audio_files(expires_at);
`;

function migrate(): void {
  console.log('Running SQLite database migrations...');

  try {
    // Execute the entire migration script at once
    db.exec(migrations);
    console.log('Migrations completed successfully!');
  } catch (error) {
    // Check if it's just "already exists" errors
    const errorMsg = String(error);
    if (errorMsg.includes('already exists')) {
      console.log('Tables already exist, migrations completed!');
    } else {
      console.error('Migration failed:', error);
      throw error;
    }
  }

  // Add columns to existing tables (for incremental schema updates)
  try {
    // Add model column to songs table if it doesn't exist
    db.exec(`ALTER TABLE songs ADD COLUMN model TEXT`);
    console.log('Added model column to songs table');
  } catch (error) {
    const errorMsg = String(error);
    if (errorMsg.includes('duplicate column name')) {
      console.log('Column model already exists in songs table');
    } else {
      console.error('Failed to add model column:', error);
    }
  }

  // Create presets table for saving/loading generation parameter presets
  try {
    db.exec(`
      CREATE TABLE IF NOT EXISTS presets (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        description TEXT,
        is_builtin INTEGER DEFAULT 0,
        category TEXT DEFAULT 'custom',
        params TEXT NOT NULL DEFAULT '{}',
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
      );
      CREATE INDEX IF NOT EXISTS idx_presets_user_id ON presets(user_id);
      CREATE INDEX IF NOT EXISTS idx_presets_category ON presets(category);
      CREATE INDEX IF NOT EXISTS idx_presets_is_builtin ON presets(is_builtin);
    `);
    console.log('Presets table created successfully');
  } catch (error) {
    const errorMsg = String(error);
    if (errorMsg.includes('already exists')) {
      console.log('Presets table already exists');
    } else {
      console.error('Failed to create presets table:', error);
    }
  }

  // Create projects table for full settings save with auto-save and rollback
  try {
    db.exec(`
      CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        description TEXT,
        params TEXT NOT NULL DEFAULT '{}',
        is_active INTEGER DEFAULT 0,
        auto_save_enabled INTEGER DEFAULT 1,
        auto_save_interval INTEGER DEFAULT 60,
        auto_save_max_count INTEGER DEFAULT 50,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
      );
      CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
      CREATE INDEX IF NOT EXISTS idx_projects_is_active ON projects(is_active);
    `);
    console.log('Projects table created successfully');
  } catch (error) {
    const errorMsg = String(error);
    if (errorMsg.includes('already exists')) {
      console.log('Projects table already exists');
    } else {
      console.error('Failed to create projects table:', error);
    }
  }

  // Create project_snapshots table for auto-save history and rollback
  try {
    db.exec(`
      CREATE TABLE IF NOT EXISTS project_snapshots (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
        label TEXT,
        params TEXT NOT NULL DEFAULT '{}',
        is_auto INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
      );
      CREATE INDEX IF NOT EXISTS idx_snapshots_project_id ON project_snapshots(project_id);
      CREATE INDEX IF NOT EXISTS idx_snapshots_created_at ON project_snapshots(created_at);
    `);
    console.log('Project snapshots table created successfully');
  } catch (error) {
    const errorMsg = String(error);
    if (errorMsg.includes('already exists')) {
      console.log('Project snapshots table already exists');
    } else {
      console.error('Failed to create project snapshots table:', error);
    }
  }

  // Create project_changelogs table for tracking parameter changes (git-like)
  try {
    db.exec(`
      CREATE TABLE IF NOT EXISTS project_changelogs (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
        action TEXT NOT NULL,
        label TEXT,
        changes TEXT NOT NULL DEFAULT '{}',
        snapshot_params TEXT NOT NULL DEFAULT '{}',
        created_at TEXT DEFAULT (datetime('now'))
      );
      CREATE INDEX IF NOT EXISTS idx_changelogs_project_id ON project_changelogs(project_id);
      CREATE INDEX IF NOT EXISTS idx_changelogs_created_at ON project_changelogs(created_at);
    `);
    console.log('Project changelogs table created successfully');
  } catch (error) {
    const errorMsg = String(error);
    if (errorMsg.includes('already exists')) {
      console.log('Project changelogs table already exists');
    } else {
      console.error('Failed to create project changelogs table:', error);
    }
  }

  // Add is_default column to projects table
  try {
    db.exec(`ALTER TABLE projects ADD COLUMN is_default INTEGER DEFAULT 0`);
    console.log('Added is_default column to projects table');
  } catch (error) {
    const errorMsg = String(error);
    if (errorMsg.includes('duplicate column name')) {
      console.log('Column is_default already exists in projects table');
    } else {
      console.error('Failed to add is_default column:', error);
    }
  }

  // Add um_uid column to users table (links local user to 云集 UM account)
  try {
    db.exec(`ALTER TABLE users ADD COLUMN um_uid TEXT`);
    console.log('Added um_uid column to users table');
  } catch (error) {
    const errorMsg = String(error);
    if (errorMsg.includes('duplicate column name')) {
      console.log('Column um_uid already exists in users table');
    } else {
      console.error('Failed to add um_uid column:', error);
    }
  }
}

// Run migrations
migrate();
