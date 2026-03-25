/**
 * 图谱可视化工具函数
 * 用于 AssetForceGraph 组件的节点/边类型映射和样式配置
 */

// 节点类型到 SVG 形状的映射
export const NODE_SHAPES = {
  asset: 'circle',
  project: 'rect',
  shot: 'diamond',
  category: 'hexagon',
  person: 'circle-sm',
  style: 'rounded-rect',
  prompt: 'rounded-rect'
}

// 节点类型到默认颜色
export const NODE_COLORS = {
  asset: '#4ECDC4',
  project: '#FF6B6B',
  shot: '#FFE66D',
  category: '#A78BFA',
  person: '#60A5FA',
  style: '#F472B6',
  prompt: '#34D399'
}

// 边类型到线条样式
export const LINK_STYLES = {
  contains: 'solid',
  belongs_to: 'dashed',
  references: 'arrow-solid',
  derived_from: 'arrow-dashed',
  same_style: 'dotted',
  similar_to: 'dotted',
  co_occurs: 'transparent-thin'
}

// 边类型中文标签
export const LINK_LABELS = {
  contains: '包含',
  belongs_to: '属于',
  references: '引用',
  derived_from: '派生自',
  same_style: '同风格',
  similar_to: '相似',
  co_occurs: '共现'
}

// 节点类型中文标签
export const NODE_LABELS = {
  asset: '资产',
  project: '项目',
  shot: '镜头',
  category: '分类',
  person: '人员',
  style: '风格',
  prompt: '提示词'
}

// 节点类型到默认大小（半径或宽度）
export const NODE_SIZES = {
  asset: 20,
  project: 30,
  shot: 22,
  category: 24,
  person: 12,
  style: 28,
  prompt: 28
}

/**
 * 获取节点的显示颜色
 * 优先使用 metadata.color，否则使用类型默认色
 */
export function getNodeColor(node) {
  if (node.metadata && node.metadata.color) return node.metadata.color
  return NODE_COLORS[node.node_type] || NODE_COLORS.asset
}

/**
 * 获取节点的显示大小
 */
export function getNodeSize(node, isCenterNode = false) {
  const baseSize = NODE_SIZES[node.node_type] || 20
  return isCenterNode ? baseSize * 1.5 : baseSize
}

/**
 * 获取边的 stroke-dasharray 值
 */
export function getLinkDashArray(linkType) {
  const style = LINK_STYLES[linkType] || 'solid'
  switch (style) {
    case 'dashed':
    case 'arrow-dashed':
      return '6,3'
    case 'dotted':
      return '2,4'
    case 'transparent-thin':
      return '4,2'
    default:
      return null
  }
}

/**
 * 判断边是否需要箭头
 */
export function linkHasArrow(linkType) {
  const style = LINK_STYLES[linkType] || 'solid'
  return style === 'arrow-solid' || style === 'arrow-dashed'
}

/**
 * 获取边的不透明度
 */
export function getLinkOpacity(linkType) {
  if (linkType === 'co_occurs') return 0.3
  return 0.6
}

/**
 * 获取边宽度，由 weight 控制
 */
export function getLinkWidth(weight = 1) {
  return Math.max(1, Math.min(6, weight * 2))
}

/**
 * 生成六边形路径 (用于 category 节点)
 * @param {number} size - 六边形"半径"
 */
export function hexagonPath(size) {
  const points = []
  for (let i = 0; i < 6; i++) {
    const angle = (Math.PI / 3) * i - Math.PI / 2
    points.push([size * Math.cos(angle), size * Math.sin(angle)])
  }
  return points.map((p) => p.join(',')).join(' ')
}

/**
 * 生成菱形路径 (用于 shot 节点)
 * @param {number} size - 菱形"半径"
 */
export function diamondPath(size) {
  return `${0},${-size} ${size},${0} ${0},${size} ${-size},${0}`
}
