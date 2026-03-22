/**
 * In-memory data store for local development.
 * Will be replaced by Cloudflare D1 + Drizzle ORM in production.
 */

interface User {
  id: string;
  phone: string;
  passwordHash: string;
  nickname: string;
  avatarUrl: string | null;
  role: "admin" | "director" | "artist" | "readonly";
  inviteCodeUsed: string;
  createdAt: string;
  updatedAt: string;
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

interface DbStore {
  users: User[];
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
}

// Singleton store with seed data
let store: DbStore | null = null;

export function getDb(): DbStore {
  if (!store) {
    store = {
      users: [
        {
          id: "usr_admin",
          phone: "13800000000",
          // password: admin123
          passwordHash:
            "$2a$10$6KqFHo4v3sBxEz3FH3L1MOKkj3w4jGVTzJ1h5J.1j2ZrYVqQqL2jS",
          nickname: "管理员",
          avatarUrl: null,
          role: "admin",
          inviteCodeUsed: "SEED",
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        },
      ],
      inviteCodes: [
        {
          id: "inv_seed",
          code: "HUAZONG2026",
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
    };
  }
  return store;
}
