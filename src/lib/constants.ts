/** Shot status definitions with labels and colors */
export const SHOT_STATUS = {
  pending_upload: { label: "待上传", color: "bg-yellow-100 text-yellow-800" },
  pending_review: { label: "待审查", color: "bg-blue-100 text-blue-800" },
  needs_revision: { label: "需修改", color: "bg-red-100 text-red-800" },
  revised_pending_review: { label: "已修改待复审", color: "bg-purple-100 text-purple-800" },
  approved: { label: "通过", color: "bg-green-100 text-green-800" },
  delivered: { label: "已交付", color: "bg-gray-100 text-gray-800" },
} as const;

export type ShotStatus = keyof typeof SHOT_STATUS;

/** User roles */
export const USER_ROLES = {
  admin: { label: "管理员", level: 100 },
  director: { label: "导演", level: 50 },
  artist: { label: "美术", level: 20 },
  readonly: { label: "只读", level: 0 },
} as const;

export type UserRole = keyof typeof USER_ROLES;

/** Project status */
export const PROJECT_STATUS = {
  active: { label: "进行中", color: "bg-green-100 text-green-800" },
  completed: { label: "已完成", color: "bg-blue-100 text-blue-800" },
  archived: { label: "已归档", color: "bg-gray-100 text-gray-800" },
} as const;

export type ProjectStatus = keyof typeof PROJECT_STATUS;

/** Task priority */
export const TASK_PRIORITY = {
  low: { label: "低", color: "text-gray-500" },
  medium: { label: "中", color: "text-yellow-600" },
  high: { label: "高", color: "text-red-600" },
} as const;

/** Credit platforms */
export const CREDIT_PLATFORMS = [
  "即梦 (Seedance)",
  "可灵 (Kling)",
  "Midjourney",
  "Flux",
  "ComfyUI",
  "Gemini",
  "海螺 (Hailuo)",
  "Vidu",
  "其他",
] as const;

/** Annotation status */
export const ANNOTATION_STATUS = {
  unresolved: { label: "未处理", color: "bg-red-100 text-red-800" },
  in_progress: { label: "处理中", color: "bg-yellow-100 text-yellow-800" },
  resolved: { label: "已解决", color: "bg-green-100 text-green-800" },
} as const;
