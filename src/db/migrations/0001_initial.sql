-- 0001_initial.sql
-- HuaZong Production Hub — Initial schema migration
-- Target: Cloudflare D1 (SQLite)

-- ============================================================
-- users
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
  id            TEXT PRIMARY KEY NOT NULL,
  phone         TEXT,
  password_hash TEXT,
  nickname      TEXT NOT NULL,
  avatar_url    TEXT,
  role          TEXT NOT NULL DEFAULT 'artist'
                CHECK (role IN ('admin', 'director', 'artist', 'readonly')),
  invite_code_used TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS users_phone_idx ON users (phone);
CREATE INDEX IF NOT EXISTS users_role_idx ON users (role);

-- ============================================================
-- invite_codes
-- ============================================================

CREATE TABLE IF NOT EXISTS invite_codes (
  id          TEXT PRIMARY KEY NOT NULL,
  code        TEXT NOT NULL UNIQUE,
  created_by  TEXT NOT NULL REFERENCES users(id),
  used_by     TEXT REFERENCES users(id),
  used_at     TEXT,
  expires_at  TEXT,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS invite_codes_code_idx ON invite_codes (code);
CREATE INDEX IF NOT EXISTS invite_codes_created_by_idx ON invite_codes (created_by);

-- ============================================================
-- projects
-- ============================================================

CREATE TABLE IF NOT EXISTS projects (
  id              TEXT PRIMARY KEY NOT NULL,
  name            TEXT NOT NULL,
  description     TEXT,
  cover_url       TEXT,
  status          TEXT NOT NULL DEFAULT 'active'
                  CHECK (status IN ('active', 'completed', 'archived')),
  style_guide_json TEXT,
  created_by      TEXT NOT NULL REFERENCES users(id),
  created_at      TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS projects_status_idx ON projects (status);
CREATE INDEX IF NOT EXISTS projects_created_by_idx ON projects (created_by);

-- ============================================================
-- project_members
-- ============================================================

CREATE TABLE IF NOT EXISTS project_members (
  project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role       TEXT NOT NULL DEFAULT 'artist'
             CHECK (role IN ('admin', 'director', 'artist', 'readonly')),
  joined_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS project_members_project_idx ON project_members (project_id);
CREATE INDEX IF NOT EXISTS project_members_user_idx ON project_members (user_id);
CREATE UNIQUE INDEX IF NOT EXISTS project_members_pk ON project_members (project_id, user_id);

-- ============================================================
-- shots
-- ============================================================

CREATE TABLE IF NOT EXISTS shots (
  id                TEXT PRIMARY KEY NOT NULL,
  project_id        TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  shot_number       INTEGER NOT NULL,
  scene_description TEXT,
  dialogue          TEXT,
  duration_seconds  INTEGER,
  camera_angle      TEXT,
  status            TEXT NOT NULL DEFAULT 'pending_upload'
                    CHECK (status IN (
                      'pending_upload', 'pending_review', 'needs_revision',
                      'revised_pending_review', 'approved', 'delivered'
                    )),
  assignee_id       TEXT REFERENCES users(id),
  sort_order        INTEGER NOT NULL DEFAULT 0,
  created_at        TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS shots_project_idx ON shots (project_id);
CREATE INDEX IF NOT EXISTS shots_status_idx ON shots (status);
CREATE INDEX IF NOT EXISTS shots_assignee_idx ON shots (assignee_id);
CREATE INDEX IF NOT EXISTS shots_project_sort_idx ON shots (project_id, sort_order);

-- ============================================================
-- assets
-- ============================================================

CREATE TABLE IF NOT EXISTS assets (
  id              TEXT PRIMARY KEY NOT NULL,
  shot_id         TEXT NOT NULL REFERENCES shots(id) ON DELETE CASCADE,
  file_url        TEXT NOT NULL,
  file_type       TEXT NOT NULL CHECK (file_type IN ('image', 'video')),
  version_number  INTEGER NOT NULL DEFAULT 1,
  thumbnail_url   TEXT,
  uploaded_by     TEXT NOT NULL REFERENCES users(id),
  created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS assets_shot_idx ON assets (shot_id);
CREATE INDEX IF NOT EXISTS assets_uploaded_by_idx ON assets (uploaded_by);
CREATE INDEX IF NOT EXISTS assets_shot_version_idx ON assets (shot_id, version_number);

-- ============================================================
-- annotations
-- ============================================================

CREATE TABLE IF NOT EXISTS annotations (
  id                 TEXT PRIMARY KEY NOT NULL,
  asset_id           TEXT NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
  canvas_data_json   TEXT,
  text_comment       TEXT,
  annotator_id       TEXT NOT NULL REFERENCES users(id),
  status             TEXT NOT NULL DEFAULT 'unresolved'
                     CHECK (status IN ('unresolved', 'in_progress', 'resolved')),
  frame_timestamp_ms INTEGER,
  created_at         TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at         TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS annotations_asset_idx ON annotations (asset_id);
CREATE INDEX IF NOT EXISTS annotations_annotator_idx ON annotations (annotator_id);
CREATE INDEX IF NOT EXISTS annotations_status_idx ON annotations (status);

-- ============================================================
-- annotation_replies
-- ============================================================

CREATE TABLE IF NOT EXISTS annotation_replies (
  id            TEXT PRIMARY KEY NOT NULL,
  annotation_id TEXT NOT NULL REFERENCES annotations(id) ON DELETE CASCADE,
  user_id       TEXT NOT NULL REFERENCES users(id),
  content       TEXT NOT NULL,
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS annotation_replies_annotation_idx ON annotation_replies (annotation_id);
CREATE INDEX IF NOT EXISTS annotation_replies_user_idx ON annotation_replies (user_id);

-- ============================================================
-- characters
-- ============================================================

CREATE TABLE IF NOT EXISTS characters (
  id          TEXT PRIMARY KEY NOT NULL,
  project_id  TEXT REFERENCES projects(id) ON DELETE CASCADE,
  name        TEXT NOT NULL,
  description TEXT,
  is_global   INTEGER NOT NULL DEFAULT 0,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS characters_project_idx ON characters (project_id);
CREATE INDEX IF NOT EXISTS characters_global_idx ON characters (is_global);

-- ============================================================
-- character_refs
-- ============================================================

CREATE TABLE IF NOT EXISTS character_refs (
  id            TEXT PRIMARY KEY NOT NULL,
  character_id  TEXT NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
  ref_image_url TEXT NOT NULL,
  ref_type      TEXT NOT NULL CHECK (ref_type IN ('front', 'side', 'full', 'closeup')),
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS character_refs_character_idx ON character_refs (character_id);

-- ============================================================
-- props
-- ============================================================

CREATE TABLE IF NOT EXISTS props (
  id          TEXT PRIMARY KEY NOT NULL,
  project_id  TEXT REFERENCES projects(id) ON DELETE CASCADE,
  name        TEXT NOT NULL,
  description TEXT,
  is_global   INTEGER NOT NULL DEFAULT 0,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS props_project_idx ON props (project_id);
CREATE INDEX IF NOT EXISTS props_global_idx ON props (is_global);

-- ============================================================
-- prop_refs
-- ============================================================

CREATE TABLE IF NOT EXISTS prop_refs (
  id            TEXT PRIMARY KEY NOT NULL,
  prop_id       TEXT NOT NULL REFERENCES props(id) ON DELETE CASCADE,
  ref_image_url TEXT NOT NULL,
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS prop_refs_prop_idx ON prop_refs (prop_id);

-- ============================================================
-- scenes
-- ============================================================

CREATE TABLE IF NOT EXISTS scenes (
  id          TEXT PRIMARY KEY NOT NULL,
  project_id  TEXT REFERENCES projects(id) ON DELETE CASCADE,
  name        TEXT NOT NULL,
  description TEXT,
  time_of_day TEXT,
  is_global   INTEGER NOT NULL DEFAULT 0,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS scenes_project_idx ON scenes (project_id);
CREATE INDEX IF NOT EXISTS scenes_global_idx ON scenes (is_global);

-- ============================================================
-- scene_refs
-- ============================================================

CREATE TABLE IF NOT EXISTS scene_refs (
  id            TEXT PRIMARY KEY NOT NULL,
  scene_id      TEXT NOT NULL REFERENCES scenes(id) ON DELETE CASCADE,
  ref_image_url TEXT NOT NULL,
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS scene_refs_scene_idx ON scene_refs (scene_id);

-- ============================================================
-- shot_relations (polymorphic join)
-- ============================================================

CREATE TABLE IF NOT EXISTS shot_relations (
  id            TEXT PRIMARY KEY NOT NULL,
  shot_id       TEXT NOT NULL REFERENCES shots(id) ON DELETE CASCADE,
  relation_type TEXT NOT NULL CHECK (relation_type IN ('character', 'prop', 'scene')),
  relation_id   TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS shot_relations_shot_idx ON shot_relations (shot_id);
CREATE INDEX IF NOT EXISTS shot_relations_type_relation_idx ON shot_relations (relation_type, relation_id);
CREATE UNIQUE INDEX IF NOT EXISTS shot_relations_unique_idx ON shot_relations (shot_id, relation_type, relation_id);

-- ============================================================
-- style_templates
-- ============================================================

CREATE TABLE IF NOT EXISTS style_templates (
  id              TEXT PRIMARY KEY NOT NULL,
  name            TEXT NOT NULL,
  tags_json       TEXT,
  keywords_json   TEXT,
  description     TEXT,
  ref_images_json TEXT,
  project_id      TEXT REFERENCES projects(id),
  created_by      TEXT NOT NULL REFERENCES users(id),
  created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS style_templates_project_idx ON style_templates (project_id);
CREATE INDEX IF NOT EXISTS style_templates_created_by_idx ON style_templates (created_by);

-- ============================================================
-- prompts
-- ============================================================

CREATE TABLE IF NOT EXISTS prompts (
  id                TEXT PRIMARY KEY NOT NULL,
  title             TEXT NOT NULL,
  content           TEXT NOT NULL,
  format            TEXT NOT NULL DEFAULT 'text'
                    CHECK (format IN ('text', 'json')),
  tags_json         TEXT,
  preview_image_url TEXT,
  usage_count       INTEGER NOT NULL DEFAULT 0,
  created_by        TEXT NOT NULL REFERENCES users(id),
  created_at        TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS prompts_created_by_idx ON prompts (created_by);
CREATE INDEX IF NOT EXISTS prompts_usage_count_idx ON prompts (usage_count);

-- ============================================================
-- credit_logs
-- ============================================================

CREATE TABLE IF NOT EXISTS credit_logs (
  id          TEXT PRIMARY KEY NOT NULL,
  user_id     TEXT NOT NULL REFERENCES users(id),
  platform    TEXT NOT NULL,
  amount      INTEGER NOT NULL,
  project_id  TEXT REFERENCES projects(id),
  note        TEXT,
  logged_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS credit_logs_user_idx ON credit_logs (user_id);
CREATE INDEX IF NOT EXISTS credit_logs_platform_idx ON credit_logs (platform);
CREATE INDEX IF NOT EXISTS credit_logs_project_idx ON credit_logs (project_id);
CREATE INDEX IF NOT EXISTS credit_logs_logged_at_idx ON credit_logs (logged_at);

-- ============================================================
-- tasks
-- ============================================================

CREATE TABLE IF NOT EXISTS tasks (
  id            TEXT PRIMARY KEY NOT NULL,
  shot_id       TEXT REFERENCES shots(id) ON DELETE SET NULL,
  annotation_id TEXT REFERENCES annotations(id) ON DELETE SET NULL,
  title         TEXT NOT NULL,
  assignee_id   TEXT REFERENCES users(id),
  status        TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'in_progress', 'completed')),
  priority      TEXT NOT NULL DEFAULT 'medium'
                CHECK (priority IN ('low', 'medium', 'high')),
  due_date      TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS tasks_shot_idx ON tasks (shot_id);
CREATE INDEX IF NOT EXISTS tasks_assignee_idx ON tasks (assignee_id);
CREATE INDEX IF NOT EXISTS tasks_status_idx ON tasks (status);
CREATE INDEX IF NOT EXISTS tasks_priority_idx ON tasks (priority);
CREATE INDEX IF NOT EXISTS tasks_due_date_idx ON tasks (due_date);

-- ============================================================
-- activity_logs
-- ============================================================

CREATE TABLE IF NOT EXISTS activity_logs (
  id           TEXT PRIMARY KEY NOT NULL,
  user_id      TEXT NOT NULL REFERENCES users(id),
  project_id   TEXT REFERENCES projects(id),
  action       TEXT NOT NULL,
  details_json TEXT,
  created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS activity_logs_user_idx ON activity_logs (user_id);
CREATE INDEX IF NOT EXISTS activity_logs_project_idx ON activity_logs (project_id);
CREATE INDEX IF NOT EXISTS activity_logs_action_idx ON activity_logs (action);
CREATE INDEX IF NOT EXISTS activity_logs_created_at_idx ON activity_logs (created_at);
