/**
 * 分镜拖拽排序管理器
 *
 * 使用原生 HTML5 DnD API 实现分镜卡片拖拽排序。
 * 支持：
 * 1. 同一场景内排序
 * 2. 跨场景移动
 * 3. 拖拽占位符
 * 4. 排序结果回调
 */

export class StoryboardDnD {
  constructor(options = {}) {
    this.onReorder = options.onReorder || (() => {})
    this.draggedShot = null
    this.draggedElement = null
    this.placeholder = null
    this.sourceSequenceId = null
  }

  /**
   * 绑定到卡片元素（在 Vue onMounted 中调用）
   */
  bindCard(el, shot, sequenceId) {
    el.draggable = true
    el.dataset.shotId = shot.id
    el.dataset.sequenceId = sequenceId

    el.addEventListener('dragstart', (e) => this._onDragStart(e, shot, sequenceId))
    el.addEventListener('dragend', (e) => this._onDragEnd(e))
    el.addEventListener('dragover', (e) => this._onDragOver(e))
    el.addEventListener('drop', (e) => this._onDrop(e))
  }

  _onDragStart(e, shot, sequenceId) {
    this.draggedShot = shot
    this.sourceSequenceId = sequenceId
    this.draggedElement = e.target

    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', shot.id)

    // 添加拖拽样式
    requestAnimationFrame(() => {
      e.target.classList.add('dragging')
    })
  }

  _onDragEnd(e) {
    e.target.classList.remove('dragging')
    this.draggedShot = null
    this.draggedElement = null
    this.sourceSequenceId = null

    // 移除所有占位符
    document.querySelectorAll('.dnd-placeholder').forEach(el => el.remove())
    document.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'))
  }

  _onDragOver(e) {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'

    const target = e.target.closest('.storyboard-card')
    if (!target || target === this.draggedElement) return

    // 计算是在目标前面还是后面
    const rect = target.getBoundingClientRect()
    const midX = rect.left + rect.width / 2

    document.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'))

    if (e.clientX < midX) {
      target.classList.add('drag-over')
      target.style.setProperty('--drag-side', 'left')
    } else {
      target.classList.add('drag-over')
      target.style.setProperty('--drag-side', 'right')
    }
  }

  _onDrop(e) {
    e.preventDefault()
    const target = e.target.closest('.storyboard-card')
    if (!target || !this.draggedShot) return

    const targetShotId = target.dataset.shotId
    const targetSequenceId = target.dataset.sequenceId

    if (targetShotId === this.draggedShot.id) return

    // 计算插入位置
    const rect = target.getBoundingClientRect()
    const insertBefore = e.clientX < rect.left + rect.width / 2

    this.onReorder({
      shotId: this.draggedShot.id,
      targetShotId,
      sourceSequenceId: this.sourceSequenceId,
      targetSequenceId,
      insertBefore
    })

    document.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'))
  }

  /**
   * 清理所有事件监听
   */
  destroy() {
    this.draggedShot = null
    this.draggedElement = null
  }
}

/**
 * 计算新的排序顺序
 * @param {Array} sequences - 当前序列数据
 * @param {Object} reorderInfo - 拖拽结果信息
 * @returns {Array} shot_orders - [{shot_id, order, sequence_id}]
 */
export function calculateNewOrder(sequences, reorderInfo) {
  const { shotId, targetShotId, sourceSequenceId, targetSequenceId, insertBefore } = reorderInfo

  // 深拷贝
  const seqs = JSON.parse(JSON.stringify(sequences))

  // 找到源和目标序列
  const sourceSeq = seqs.find(s => s.id === sourceSequenceId)
  const targetSeq = seqs.find(s => s.id === targetSequenceId)

  if (!sourceSeq || !targetSeq) return []

  // 从源序列移除
  const shotIndex = sourceSeq.shots.findIndex(s => s.id === shotId)
  if (shotIndex === -1) return []
  const [movedShot] = sourceSeq.shots.splice(shotIndex, 1)

  // 找到目标位置
  let targetIndex = targetSeq.shots.findIndex(s => s.id === targetShotId)
  if (!insertBefore) targetIndex++

  // 插入到目标序列
  targetSeq.shots.splice(targetIndex, 0, movedShot)

  // 生成新的排序列表
  const shotOrders = []
  for (const seq of seqs) {
    seq.shots.forEach((shot, idx) => {
      shotOrders.push({
        shot_id: shot.id,
        order: idx + 1,
        sequence_id: seq.id
      })
    })
  }

  return shotOrders
}
