import { sqliteTable, text, integer, index, uniqueIndex } from "drizzle-orm/sqlite-core";
import { sql } from "drizzle-orm";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const id = () => text("id").primaryKey().notNull(); // nanoid
const createdAt = () =>
  text("created_at")
    .notNull()
    .default(sql`(datetime('now'))`);
const updatedAt = () =>
  text("updated_at")
    .notNull()
    .default(sql`(datetime('now'))`);

// ---------------------------------------------------------------------------
// users
// ---------------------------------------------------------------------------

export const users = sqliteTable(
  "users",
  {
    id: id(),
    phone: text("phone"),
    passwordHash: text("password_hash"),
    nickname: text("nickname").notNull(),
    avatarUrl: text("avatar_url"),
    role: text("role", { enum: ["admin", "director", "artist", "readonly"] })
      .notNull()
      .default("artist"),
    inviteCodeUsed: text("invite_code_used"),
    createdAt: createdAt(),
    updatedAt: updatedAt(),
  },
  (t) => [
    uniqueIndex("users_phone_idx").on(t.phone),
    index("users_role_idx").on(t.role),
  ],
);

// ---------------------------------------------------------------------------
// invite_codes
// ---------------------------------------------------------------------------

export const inviteCodes = sqliteTable(
  "invite_codes",
  {
    id: id(),
    code: text("code").notNull().unique(),
    createdBy: text("created_by")
      .notNull()
      .references(() => users.id),
    usedBy: text("used_by").references(() => users.id),
    usedAt: text("used_at"),
    expiresAt: text("expires_at"),
    createdAt: createdAt(),
  },
  (t) => [
    uniqueIndex("invite_codes_code_idx").on(t.code),
    index("invite_codes_created_by_idx").on(t.createdBy),
  ],
);

// ---------------------------------------------------------------------------
// projects
// ---------------------------------------------------------------------------

export const projects = sqliteTable(
  "projects",
  {
    id: id(),
    name: text("name").notNull(),
    description: text("description"),
    coverUrl: text("cover_url"),
    status: text("status", { enum: ["active", "completed", "archived"] })
      .notNull()
      .default("active"),
    styleGuideJson: text("style_guide_json"), // JSON string
    createdBy: text("created_by")
      .notNull()
      .references(() => users.id),
    createdAt: createdAt(),
    updatedAt: updatedAt(),
  },
  (t) => [
    index("projects_status_idx").on(t.status),
    index("projects_created_by_idx").on(t.createdBy),
  ],
);

// ---------------------------------------------------------------------------
// project_members
// ---------------------------------------------------------------------------

export const projectMembers = sqliteTable(
  "project_members",
  {
    projectId: text("project_id")
      .notNull()
      .references(() => projects.id, { onDelete: "cascade" }),
    userId: text("user_id")
      .notNull()
      .references(() => users.id, { onDelete: "cascade" }),
    role: text("role", { enum: ["admin", "director", "artist", "readonly"] })
      .notNull()
      .default("artist"),
    joinedAt: text("joined_at")
      .notNull()
      .default(sql`(datetime('now'))`),
  },
  (t) => [
    index("project_members_project_idx").on(t.projectId),
    index("project_members_user_idx").on(t.userId),
    uniqueIndex("project_members_pk").on(t.projectId, t.userId),
  ],
);

// ---------------------------------------------------------------------------
// shots
// ---------------------------------------------------------------------------

export const shots = sqliteTable(
  "shots",
  {
    id: id(),
    projectId: text("project_id")
      .notNull()
      .references(() => projects.id, { onDelete: "cascade" }),
    shotNumber: integer("shot_number").notNull(),
    sceneDescription: text("scene_description"),
    dialogue: text("dialogue"),
    durationSeconds: integer("duration_seconds"),
    cameraAngle: text("camera_angle"),
    status: text("status", {
      enum: [
        "pending_upload",
        "pending_review",
        "needs_revision",
        "revised_pending_review",
        "approved",
        "delivered",
      ],
    })
      .notNull()
      .default("pending_upload"),
    assigneeId: text("assignee_id").references(() => users.id),
    sortOrder: integer("sort_order").notNull().default(0),
    createdAt: createdAt(),
    updatedAt: updatedAt(),
  },
  (t) => [
    index("shots_project_idx").on(t.projectId),
    index("shots_status_idx").on(t.status),
    index("shots_assignee_idx").on(t.assigneeId),
    index("shots_project_sort_idx").on(t.projectId, t.sortOrder),
  ],
);

// ---------------------------------------------------------------------------
// assets
// ---------------------------------------------------------------------------

export const assets = sqliteTable(
  "assets",
  {
    id: id(),
    shotId: text("shot_id")
      .notNull()
      .references(() => shots.id, { onDelete: "cascade" }),
    fileUrl: text("file_url").notNull(),
    fileType: text("file_type", { enum: ["image", "video"] }).notNull(),
    versionNumber: integer("version_number").notNull().default(1),
    thumbnailUrl: text("thumbnail_url"),
    uploadedBy: text("uploaded_by")
      .notNull()
      .references(() => users.id),
    createdAt: createdAt(),
  },
  (t) => [
    index("assets_shot_idx").on(t.shotId),
    index("assets_uploaded_by_idx").on(t.uploadedBy),
    index("assets_shot_version_idx").on(t.shotId, t.versionNumber),
  ],
);

// ---------------------------------------------------------------------------
// annotations
// ---------------------------------------------------------------------------

export const annotations = sqliteTable(
  "annotations",
  {
    id: id(),
    assetId: text("asset_id")
      .notNull()
      .references(() => assets.id, { onDelete: "cascade" }),
    canvasDataJson: text("canvas_data_json"), // Fabric.js / Konva canvas JSON
    textComment: text("text_comment"),
    annotatorId: text("annotator_id")
      .notNull()
      .references(() => users.id),
    status: text("status", {
      enum: ["unresolved", "in_progress", "resolved"],
    })
      .notNull()
      .default("unresolved"),
    frameTimestampMs: integer("frame_timestamp_ms"), // null for images
    createdAt: createdAt(),
    updatedAt: updatedAt(),
  },
  (t) => [
    index("annotations_asset_idx").on(t.assetId),
    index("annotations_annotator_idx").on(t.annotatorId),
    index("annotations_status_idx").on(t.status),
  ],
);

// ---------------------------------------------------------------------------
// annotation_replies
// ---------------------------------------------------------------------------

export const annotationReplies = sqliteTable(
  "annotation_replies",
  {
    id: id(),
    annotationId: text("annotation_id")
      .notNull()
      .references(() => annotations.id, { onDelete: "cascade" }),
    userId: text("user_id")
      .notNull()
      .references(() => users.id),
    content: text("content").notNull(),
    createdAt: createdAt(),
  },
  (t) => [
    index("annotation_replies_annotation_idx").on(t.annotationId),
    index("annotation_replies_user_idx").on(t.userId),
  ],
);

// ---------------------------------------------------------------------------
// characters
// ---------------------------------------------------------------------------

export const characters = sqliteTable(
  "characters",
  {
    id: id(),
    projectId: text("project_id").references(() => projects.id, {
      onDelete: "cascade",
    }),
    name: text("name").notNull(),
    description: text("description"),
    isGlobal: integer("is_global", { mode: "boolean" }).notNull().default(false),
    createdAt: createdAt(),
  },
  (t) => [
    index("characters_project_idx").on(t.projectId),
    index("characters_global_idx").on(t.isGlobal),
  ],
);

// ---------------------------------------------------------------------------
// character_refs
// ---------------------------------------------------------------------------

export const characterRefs = sqliteTable(
  "character_refs",
  {
    id: id(),
    characterId: text("character_id")
      .notNull()
      .references(() => characters.id, { onDelete: "cascade" }),
    refImageUrl: text("ref_image_url").notNull(),
    refType: text("ref_type", {
      enum: ["front", "side", "full", "closeup"],
    }).notNull(),
    createdAt: createdAt(),
  },
  (t) => [index("character_refs_character_idx").on(t.characterId)],
);

// ---------------------------------------------------------------------------
// props
// ---------------------------------------------------------------------------

export const props = sqliteTable(
  "props",
  {
    id: id(),
    projectId: text("project_id").references(() => projects.id, {
      onDelete: "cascade",
    }),
    name: text("name").notNull(),
    description: text("description"),
    isGlobal: integer("is_global", { mode: "boolean" }).notNull().default(false),
    createdAt: createdAt(),
  },
  (t) => [
    index("props_project_idx").on(t.projectId),
    index("props_global_idx").on(t.isGlobal),
  ],
);

// ---------------------------------------------------------------------------
// prop_refs
// ---------------------------------------------------------------------------

export const propRefs = sqliteTable(
  "prop_refs",
  {
    id: id(),
    propId: text("prop_id")
      .notNull()
      .references(() => props.id, { onDelete: "cascade" }),
    refImageUrl: text("ref_image_url").notNull(),
    createdAt: createdAt(),
  },
  (t) => [index("prop_refs_prop_idx").on(t.propId)],
);

// ---------------------------------------------------------------------------
// scenes
// ---------------------------------------------------------------------------

export const scenes = sqliteTable(
  "scenes",
  {
    id: id(),
    projectId: text("project_id").references(() => projects.id, {
      onDelete: "cascade",
    }),
    name: text("name").notNull(),
    description: text("description"),
    timeOfDay: text("time_of_day"),
    isGlobal: integer("is_global", { mode: "boolean" }).notNull().default(false),
    createdAt: createdAt(),
  },
  (t) => [
    index("scenes_project_idx").on(t.projectId),
    index("scenes_global_idx").on(t.isGlobal),
  ],
);

// ---------------------------------------------------------------------------
// scene_refs
// ---------------------------------------------------------------------------

export const sceneRefs = sqliteTable(
  "scene_refs",
  {
    id: id(),
    sceneId: text("scene_id")
      .notNull()
      .references(() => scenes.id, { onDelete: "cascade" }),
    refImageUrl: text("ref_image_url").notNull(),
    createdAt: createdAt(),
  },
  (t) => [index("scene_refs_scene_idx").on(t.sceneId)],
);

// ---------------------------------------------------------------------------
// shot_relations (polymorphic join: shot <-> character/prop/scene)
// ---------------------------------------------------------------------------

export const shotRelations = sqliteTable(
  "shot_relations",
  {
    id: id(),
    shotId: text("shot_id")
      .notNull()
      .references(() => shots.id, { onDelete: "cascade" }),
    relationType: text("relation_type", {
      enum: ["character", "prop", "scene"],
    }).notNull(),
    relationId: text("relation_id").notNull(), // FK to characters/props/scenes
  },
  (t) => [
    index("shot_relations_shot_idx").on(t.shotId),
    index("shot_relations_type_relation_idx").on(
      t.relationType,
      t.relationId,
    ),
    uniqueIndex("shot_relations_unique_idx").on(
      t.shotId,
      t.relationType,
      t.relationId,
    ),
  ],
);

// ---------------------------------------------------------------------------
// style_templates
// ---------------------------------------------------------------------------

export const styleTemplates = sqliteTable(
  "style_templates",
  {
    id: id(),
    name: text("name").notNull(),
    tagsJson: text("tags_json"), // JSON array of tag strings
    keywordsJson: text("keywords_json"), // JSON object of style keywords
    description: text("description"),
    refImagesJson: text("ref_images_json"), // JSON array of image URLs
    projectId: text("project_id").references(() => projects.id),
    createdBy: text("created_by")
      .notNull()
      .references(() => users.id),
    createdAt: createdAt(),
  },
  (t) => [
    index("style_templates_project_idx").on(t.projectId),
    index("style_templates_created_by_idx").on(t.createdBy),
  ],
);

// ---------------------------------------------------------------------------
// prompts
// ---------------------------------------------------------------------------

export const prompts = sqliteTable(
  "prompts",
  {
    id: id(),
    title: text("title").notNull(),
    content: text("content").notNull(),
    format: text("format", { enum: ["text", "json"] })
      .notNull()
      .default("text"),
    tagsJson: text("tags_json"), // JSON array of tag strings
    previewImageUrl: text("preview_image_url"),
    usageCount: integer("usage_count").notNull().default(0),
    createdBy: text("created_by")
      .notNull()
      .references(() => users.id),
    createdAt: createdAt(),
    updatedAt: updatedAt(),
  },
  (t) => [
    index("prompts_created_by_idx").on(t.createdBy),
    index("prompts_usage_count_idx").on(t.usageCount),
  ],
);

// ---------------------------------------------------------------------------
// credit_logs
// ---------------------------------------------------------------------------

export const creditLogs = sqliteTable(
  "credit_logs",
  {
    id: id(),
    userId: text("user_id")
      .notNull()
      .references(() => users.id),
    platform: text("platform").notNull(),
    amount: integer("amount").notNull(),
    projectId: text("project_id").references(() => projects.id),
    note: text("note"),
    loggedAt: text("logged_at")
      .notNull()
      .default(sql`(datetime('now'))`),
  },
  (t) => [
    index("credit_logs_user_idx").on(t.userId),
    index("credit_logs_platform_idx").on(t.platform),
    index("credit_logs_project_idx").on(t.projectId),
    index("credit_logs_logged_at_idx").on(t.loggedAt),
  ],
);

// ---------------------------------------------------------------------------
// tasks
// ---------------------------------------------------------------------------

export const tasks = sqliteTable(
  "tasks",
  {
    id: id(),
    shotId: text("shot_id").references(() => shots.id, {
      onDelete: "set null",
    }),
    annotationId: text("annotation_id").references(() => annotations.id, {
      onDelete: "set null",
    }),
    title: text("title").notNull(),
    assigneeId: text("assignee_id").references(() => users.id),
    status: text("status", {
      enum: ["pending", "in_progress", "completed"],
    })
      .notNull()
      .default("pending"),
    priority: text("priority", { enum: ["low", "medium", "high"] })
      .notNull()
      .default("medium"),
    dueDate: text("due_date"),
    createdAt: createdAt(),
    updatedAt: updatedAt(),
  },
  (t) => [
    index("tasks_shot_idx").on(t.shotId),
    index("tasks_assignee_idx").on(t.assigneeId),
    index("tasks_status_idx").on(t.status),
    index("tasks_priority_idx").on(t.priority),
    index("tasks_due_date_idx").on(t.dueDate),
  ],
);

// ---------------------------------------------------------------------------
// activity_logs
// ---------------------------------------------------------------------------

export const activityLogs = sqliteTable(
  "activity_logs",
  {
    id: id(),
    userId: text("user_id")
      .notNull()
      .references(() => users.id),
    projectId: text("project_id").references(() => projects.id),
    action: text("action").notNull(),
    detailsJson: text("details_json"), // JSON payload
    createdAt: createdAt(),
  },
  (t) => [
    index("activity_logs_user_idx").on(t.userId),
    index("activity_logs_project_idx").on(t.projectId),
    index("activity_logs_action_idx").on(t.action),
    index("activity_logs_created_at_idx").on(t.createdAt),
  ],
);
