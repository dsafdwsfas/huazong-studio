/**
 * SQLite persistent store using better-sqlite3.
 * Data is stored in /opt/huazong-studio/data/huazong.db (production)
 * or ./data/huazong.db (development).
 */

import Database from "better-sqlite3";
import path from "path";
import fs from "fs";

// ---------------------------------------------------------------------------
// Database singleton
// ---------------------------------------------------------------------------

let _db: Database.Database | null = null;

function getDatabase(): Database.Database {
  if (!_db) {
    const dataDir = path.resolve(process.cwd(), "data");
    if (!fs.existsSync(dataDir)) {
      fs.mkdirSync(dataDir, { recursive: true });
    }
    const dbPath = path.join(dataDir, "huazong.db");
    _db = new Database(dbPath);
    _db.pragma("journal_mode = WAL");
    _db.pragma("foreign_keys = ON");
    initSchema(_db);
    seedData(_db);
  }
  return _db;
}

// ---------------------------------------------------------------------------
// Schema initialization
// ---------------------------------------------------------------------------

function initSchema(db: Database.Database) {
  db.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id TEXT PRIMARY KEY NOT NULL,
      email TEXT NOT NULL,
      phone TEXT,
      nickname TEXT NOT NULL,
      avatar_url TEXT,
      role TEXT NOT NULL DEFAULT 'artist' CHECK (role IN ('admin','director','artist','readonly')),
      invite_code_used TEXT,
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE UNIQUE INDEX IF NOT EXISTS users_email_idx ON users(email);

    CREATE TABLE IF NOT EXISTS verification_codes (
      id TEXT PRIMARY KEY NOT NULL,
      email TEXT NOT NULL,
      code TEXT NOT NULL,
      expires_at TEXT NOT NULL,
      used INTEGER NOT NULL DEFAULT 0,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE INDEX IF NOT EXISTS vc_email_idx ON verification_codes(email);

    CREATE TABLE IF NOT EXISTS invite_codes (
      id TEXT PRIMARY KEY NOT NULL,
      code TEXT NOT NULL UNIQUE,
      created_by TEXT NOT NULL REFERENCES users(id),
      used_by TEXT REFERENCES users(id),
      used_at TEXT,
      expires_at TEXT,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS projects (
      id TEXT PRIMARY KEY NOT NULL,
      name TEXT NOT NULL,
      description TEXT,
      cover_url TEXT,
      status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','completed','archived')),
      style_guide_json TEXT,
      created_by TEXT NOT NULL REFERENCES users(id),
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS project_members (
      project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
      user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      role TEXT NOT NULL DEFAULT 'artist',
      joined_at TEXT NOT NULL DEFAULT (datetime('now')),
      PRIMARY KEY (project_id, user_id)
    );

    CREATE TABLE IF NOT EXISTS shots (
      id TEXT PRIMARY KEY NOT NULL,
      project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
      shot_number INTEGER NOT NULL,
      scene_description TEXT,
      dialogue TEXT,
      duration_seconds INTEGER,
      camera_angle TEXT,
      status TEXT NOT NULL DEFAULT 'pending_upload',
      assignee_id TEXT REFERENCES users(id),
      sort_order INTEGER NOT NULL DEFAULT 0,
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE INDEX IF NOT EXISTS shots_project_idx ON shots(project_id);

    CREATE TABLE IF NOT EXISTS assets (
      id TEXT PRIMARY KEY NOT NULL,
      shot_id TEXT NOT NULL REFERENCES shots(id) ON DELETE CASCADE,
      file_url TEXT NOT NULL,
      file_type TEXT NOT NULL CHECK (file_type IN ('image','video')),
      version_number INTEGER NOT NULL DEFAULT 1,
      thumbnail_url TEXT,
      uploaded_by TEXT NOT NULL REFERENCES users(id),
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE INDEX IF NOT EXISTS assets_shot_idx ON assets(shot_id);

    CREATE TABLE IF NOT EXISTS annotations (
      id TEXT PRIMARY KEY NOT NULL,
      asset_id TEXT NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
      canvas_data_json TEXT,
      text_comment TEXT,
      annotator_id TEXT NOT NULL REFERENCES users(id),
      status TEXT NOT NULL DEFAULT 'unresolved',
      frame_timestamp_ms INTEGER,
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS annotation_replies (
      id TEXT PRIMARY KEY NOT NULL,
      annotation_id TEXT NOT NULL REFERENCES annotations(id) ON DELETE CASCADE,
      user_id TEXT NOT NULL REFERENCES users(id),
      content TEXT NOT NULL,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS characters (
      id TEXT PRIMARY KEY NOT NULL,
      project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
      name TEXT NOT NULL,
      description TEXT,
      is_global INTEGER NOT NULL DEFAULT 0,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS character_refs (
      id TEXT PRIMARY KEY NOT NULL,
      character_id TEXT NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
      ref_image_url TEXT NOT NULL,
      ref_type TEXT NOT NULL,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS props (
      id TEXT PRIMARY KEY NOT NULL,
      project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
      name TEXT NOT NULL,
      description TEXT,
      is_global INTEGER NOT NULL DEFAULT 0,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS prop_refs (
      id TEXT PRIMARY KEY NOT NULL,
      prop_id TEXT NOT NULL REFERENCES props(id) ON DELETE CASCADE,
      ref_image_url TEXT NOT NULL,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS scenes (
      id TEXT PRIMARY KEY NOT NULL,
      project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
      name TEXT NOT NULL,
      description TEXT,
      time_of_day TEXT,
      is_global INTEGER NOT NULL DEFAULT 0,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS scene_refs (
      id TEXT PRIMARY KEY NOT NULL,
      scene_id TEXT NOT NULL REFERENCES scenes(id) ON DELETE CASCADE,
      ref_image_url TEXT NOT NULL,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS shot_relations (
      id TEXT PRIMARY KEY NOT NULL,
      shot_id TEXT NOT NULL REFERENCES shots(id) ON DELETE CASCADE,
      relation_type TEXT NOT NULL,
      relation_id TEXT NOT NULL,
      UNIQUE(shot_id, relation_type, relation_id)
    );

    CREATE TABLE IF NOT EXISTS style_templates (
      id TEXT PRIMARY KEY NOT NULL,
      name TEXT NOT NULL,
      tags_json TEXT,
      keywords_json TEXT,
      description TEXT,
      ref_images_json TEXT,
      project_id TEXT REFERENCES projects(id),
      created_by TEXT NOT NULL REFERENCES users(id),
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS prompts (
      id TEXT PRIMARY KEY NOT NULL,
      title TEXT NOT NULL,
      content TEXT NOT NULL,
      format TEXT NOT NULL DEFAULT 'text',
      tags_json TEXT,
      preview_image_url TEXT,
      usage_count INTEGER NOT NULL DEFAULT 0,
      created_by TEXT NOT NULL REFERENCES users(id),
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS credit_logs (
      id TEXT PRIMARY KEY NOT NULL,
      user_id TEXT NOT NULL REFERENCES users(id),
      platform TEXT NOT NULL,
      amount INTEGER NOT NULL,
      project_id TEXT REFERENCES projects(id),
      note TEXT,
      logged_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS tasks (
      id TEXT PRIMARY KEY NOT NULL,
      project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
      shot_id TEXT REFERENCES shots(id) ON DELETE SET NULL,
      annotation_id TEXT REFERENCES annotations(id) ON DELETE SET NULL,
      title TEXT NOT NULL,
      assignee_id TEXT REFERENCES users(id),
      status TEXT NOT NULL DEFAULT 'pending',
      priority TEXT NOT NULL DEFAULT 'medium',
      due_date TEXT,
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE INDEX IF NOT EXISTS tasks_project_idx ON tasks(project_id);

    CREATE TABLE IF NOT EXISTS activity_logs (
      id TEXT PRIMARY KEY NOT NULL,
      user_id TEXT NOT NULL REFERENCES users(id),
      project_id TEXT REFERENCES projects(id),
      action TEXT NOT NULL,
      details_json TEXT,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE INDEX IF NOT EXISTS activity_logs_created_idx ON activity_logs(created_at);
  `);
}

// ---------------------------------------------------------------------------
// Seed data
// ---------------------------------------------------------------------------

function seedData(db: Database.Database) {
  const adminEmail = process.env.ADMIN_EMAIL || "aa13568021@gmail.com";
  const inviteCode = process.env.INVITE_CODE || "HUAZONG2026";

  // Only seed if no admin exists
  const existing = db.prepare("SELECT id FROM users WHERE id = ?").get("usr_admin");
  if (existing) return;

  db.prepare(`
    INSERT INTO users (id, email, nickname, role, invite_code_used)
    VALUES (?, ?, '管理员', 'admin', 'SEED')
  `).run("usr_admin", adminEmail);

  db.prepare(`
    INSERT INTO invite_codes (id, code, created_by)
    VALUES (?, ?, 'usr_admin')
  `).run("inv_seed", inviteCode);
}

// ---------------------------------------------------------------------------
// Query helpers — compatible API with the old in-memory store
// ---------------------------------------------------------------------------

export interface SqliteDb {
  raw: Database.Database;

  // Query helpers
  get<T>(sql: string, ...params: unknown[]): T | undefined;
  all<T>(sql: string, ...params: unknown[]): T[];
  run(sql: string, ...params: unknown[]): Database.RunResult;
  prepare(sql: string): Database.Statement;
}

export function getDb(): SqliteDb {
  const db = getDatabase();
  return {
    raw: db,
    get<T>(sql: string, ...params: unknown[]): T | undefined {
      return db.prepare(sql).get(...params) as T | undefined;
    },
    all<T>(sql: string, ...params: unknown[]): T[] {
      return db.prepare(sql).all(...params) as T[];
    },
    run(sql: string, ...params: unknown[]): Database.RunResult {
      return db.prepare(sql).run(...params);
    },
    prepare(sql: string): Database.Statement {
      return db.prepare(sql);
    },
  };
}
