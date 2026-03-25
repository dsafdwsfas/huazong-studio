/**
 * 分类图标和颜色映射
 * 与后端预设分类保持一致（AssetCategory model）
 *
 * 图标使用 Lucide 风格内联 SVG，24x24 viewBox，stroke-width=2，currentColor
 * 不依赖外部图标库
 */

const CATEGORY_ICONS = {
  user: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
  image:
    '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>',
  box: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/></svg>',
  zap: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z"/></svg>',
  music:
    '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>',
  'message-square':
    '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>',
  palette:
    '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="13.5" cy="6.5" r="0.5" fill="currentColor"/><circle cx="17.5" cy="10.5" r="0.5" fill="currentColor"/><circle cx="8.5" cy="7.5" r="0.5" fill="currentColor"/><circle cx="6.5" cy="12.5" r="0.5" fill="currentColor"/><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2z"/></svg>',
  video:
    '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m16 13 5.223 3.482a.5.5 0 0 0 .777-.416V7.87a.5.5 0 0 0-.752-.432L16 10.5"/><rect x="2" y="6" width="14" height="12" rx="2"/></svg>',
  folder:
    '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2z"/></svg>'
}

/**
 * Default color palette for categories (hex values)
 */
const DEFAULT_COLORS = {
  '#3B82F6': { bg: 'rgba(59, 130, 246, 0.15)', text: '#3B82F6' },
  '#10B981': { bg: 'rgba(16, 185, 129, 0.15)', text: '#10B981' },
  '#F59E0B': { bg: 'rgba(245, 158, 11, 0.15)', text: '#F59E0B' },
  '#EF4444': { bg: 'rgba(239, 68, 68, 0.15)', text: '#EF4444' },
  '#8B5CF6': { bg: 'rgba(139, 92, 246, 0.15)', text: '#8B5CF6' },
  '#EC4899': { bg: 'rgba(236, 72, 153, 0.15)', text: '#EC4899' },
  '#06B6D4': { bg: 'rgba(6, 182, 212, 0.15)', text: '#06B6D4' },
  '#F97316': { bg: 'rgba(249, 115, 22, 0.15)', text: '#F97316' }
}

const FALLBACK_COLOR = { bg: 'rgba(107, 114, 128, 0.15)', text: '#6B7280' }

/**
 * Get the inline SVG for a category icon name.
 *
 * @param {string} iconName - Icon identifier (e.g. 'user', 'image', 'box')
 * @returns {string} SVG markup string, or folder icon as fallback
 */
export function getCategoryIcon(iconName) {
  if (!iconName) return CATEGORY_ICONS.folder
  return CATEGORY_ICONS[iconName] || CATEGORY_ICONS.folder
}

/**
 * Get background and text colors for a category color hex value.
 *
 * @param {string} color - Hex color string (e.g. '#3B82F6')
 * @returns {{ bg: string, text: string }} Background (with alpha) and text color
 */
export function getCategoryColor(color) {
  if (!color) return FALLBACK_COLOR
  if (DEFAULT_COLORS[color]) return DEFAULT_COLORS[color]
  // Generate from arbitrary hex
  return {
    bg: color + '26', // ~15% alpha
    text: color
  }
}

/**
 * Get display label from a category object, preferring Chinese name.
 *
 * @param {Object} category - Category object { name, name_en, slug, ... }
 * @returns {string} Display name
 */
export function getCategoryLabel(category) {
  if (!category) return '未分类'
  if (typeof category === 'string') return category
  return category.name || category.name_en || category.slug || '未分类'
}

export { CATEGORY_ICONS }
