/**
 * In-memory data store for local development.
 * Will be replaced by Cloudflare D1 + Drizzle ORM in production.
 */

interface User {
  id: string;
  email: string;
  phone: string | null;
  nickname: string;
  avatarUrl: string | null;
  role: "admin" | "director" | "artist" | "readonly";
  inviteCodeUsed: string;
  createdAt: string;
  updatedAt: string;
}

interface VerificationCode {
  id: string;
  email: string;
  code: string;
  expiresAt: string;
  used: boolean;
  createdAt: string;
}

interface InviteCode {
  id: string;
  code: string;
  createdBy: string;
  usedBy: string | null;
  usedAt: string | null;
  expiresAt: string | null;
  createdAt: string;
}

interface Project {
  id: string;
  name: string;
  description: string;
  coverUrl: string | null;
  status: "active" | "completed" | "archived";
  styleGuideJson: string | null;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
}

interface ProjectMember {
  projectId: string;
  userId: string;
  role: string;
  joinedAt: string;
}

interface Shot {
  id: string;
  projectId: string;
  shotNumber: number;
  sceneDescription: string;
  dialogue: string | null;
  durationSeconds: number | null;
  cameraAngle: string | null;
  status: string;
  assigneeId: string | null;
  sortOrder: number;
  createdAt: string;
  updatedAt: string;
}

interface Asset {
  id: string;
  shotId: string;
  fileUrl: string;
  fileType: "image" | "video";
  versionNumber: number;
  thumbnailUrl: string | null;
  uploadedBy: string;
  createdAt: string;
}

interface Annotation {
  id: string;
  assetId: string;
  canvasDataJson: string | null;
  textComment: string;
  annotatorId: string;
  status: "unresolved" | "in_progress" | "resolved";
  frameTimestampMs: number | null;
  createdAt: string;
  updatedAt: string;
}

interface AnnotationReply {
  id: string;
  annotationId: string;
  userId: string;
  content: string;
  createdAt: string;
}

interface Character {
  id: string;
  projectId: string | null;
  name: string;
  description: string | null;
  isGlobal: boolean;
  createdAt: string;
}

interface CharacterRef {
  id: string;
  characterId: string;
  refImageUrl: string;
  refType: "front" | "side" | "full" | "closeup";
  createdAt: string;
}

interface Prop {
  id: string;
  projectId: string | null;
  name: string;
  description: string | null;
  isGlobal: boolean;
  createdAt: string;
}

interface PropRef {
  id: string;
  propId: string;
  refImageUrl: string;
  createdAt: string;
}

interface Scene {
  id: string;
  projectId: string | null;
  name: string;
  description: string | null;
  timeOfDay: string | null;
  isGlobal: boolean;
  createdAt: string;
}

interface SceneRef {
  id: string;
  sceneId: string;
  refImageUrl: string;
  createdAt: string;
}

interface ShotRelation {
  id: string;
  shotId: string;
  relationType: "character" | "prop" | "scene";
  relationId: string;
}

interface Task {
  id: string;
  projectId: string;
  shotId: string | null;
  annotationId: string | null;
  title: string;
  assigneeId: string | null;
  status: "pending" | "in_progress" | "completed";
  priority: "low" | "medium" | "high";
  dueDate: string | null;
  createdAt: string;
  updatedAt: string;
}

interface CreditLog {
  id: string;
  userId: string;
  platform: string;
  amount: number;
  projectId: string | null;
  note: string | null;
  loggedAt: string;
}

interface StyleTemplate {
  id: string;
  name: string;
  tagsJson: string;
  keywordsJson: string;
  description: string;
  refImagesJson: string | null;
  projectId: string | null;
  createdBy: string;
  createdAt: string;
}

interface Prompt {
  id: string;
  title: string;
  content: string;
  format: "text" | "json";
  tagsJson: string;
  previewImageUrl: string | null;
  usageCount: number;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
}

interface ActivityLog {
  id: string;
  userId: string;
  projectId: string | null;
  action: string;
  detailsJson: string | null;
  createdAt: string;
}

export interface DbStore {
  users: User[];
  verificationCodes: VerificationCode[];
  inviteCodes: InviteCode[];
  projects: Project[];
  projectMembers: ProjectMember[];
  shots: Shot[];
  assets: Asset[];
  annotations: Annotation[];
  annotationReplies: AnnotationReply[];
  characters: Character[];
  characterRefs: CharacterRef[];
  props: Prop[];
  propRefs: PropRef[];
  scenes: Scene[];
  sceneRefs: SceneRef[];
  shotRelations: ShotRelation[];
  tasks: Task[];
  creditLogs: CreditLog[];
  styleTemplates: StyleTemplate[];
  prompts: Prompt[];
  activityLogs: ActivityLog[];
}

// Singleton store with seed data
let store: DbStore | null = null;

export function getDb(): DbStore {
  if (!store) {
    store = {
      users: [
        {
          id: "usr_admin",
          email: process.env.ADMIN_EMAIL || "aa13568021@gmail.com",
          phone: null,
          nickname: "管理员",
          avatarUrl: null,
          role: "admin",
          inviteCodeUsed: "SEED",
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        },
      ],
      verificationCodes: [],
      inviteCodes: [
        {
          id: "inv_seed",
          code: process.env.INVITE_CODE || "HUAZONG2026",
          createdBy: "usr_admin",
          usedBy: null,
          usedAt: null,
          expiresAt: null,
          createdAt: new Date().toISOString(),
        },
      ],
      projects: [],
      projectMembers: [],
      shots: [],
      assets: [],
      annotations: [],
      annotationReplies: [],
      characters: [],
      characterRefs: [],
      props: [],
      propRefs: [],
      scenes: [],
      sceneRefs: [],
      shotRelations: [],
      tasks: [],
      creditLogs: [],
      styleTemplates: [],
      prompts: [],
      activityLogs: [],
    };
  }
  return store;
}
