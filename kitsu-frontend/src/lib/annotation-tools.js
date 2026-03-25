/**
 * 分镜标注扩展工具集
 *
 * 在 Kitsu 现有 Fabric.js 标注系统上新增：
 * - 矩形框选 (Rectangle)
 * - 圆形框选 (Circle/Ellipse)
 * - 箭头 (Arrow - 运镜方向/视线引导)
 * - 标记点 (Marker - 带编号注意点)
 * - 测量工具 (Measure - 构图比例)
 *
 * 每个工具函数接受 canvas + options，设置事件处理器，
 * 返回 cleanup 函数以移除处理器。
 * 所有创建的对象设置 objectType 以支持序列化。
 */

import { fabric } from 'fabric'

// ---------------------------------------------------------------------------
// Tool 1: Rectangle
// ---------------------------------------------------------------------------

/**
 * Enable rectangle drawing tool on the canvas.
 * Click and drag to draw a rectangle.
 *
 * @param {fabric.Canvas} canvas - The Fabric.js canvas instance
 * @param {Object} options
 * @param {string} options.color - Stroke color (default '#ff3860')
 * @param {number} options.strokeWidth - Stroke width (default 2)
 * @returns {Function} Cleanup function to disable the tool
 */
export function enableRectangleTool(canvas, options = {}) {
  const { color = '#ff3860', strokeWidth = 2 } = options
  let isDrawing = false
  let startX = 0
  let startY = 0
  let rect = null

  canvas.isDrawingMode = false
  canvas.selection = false
  canvas.defaultCursor = 'crosshair'
  canvas.forEachObject(obj => {
    obj.selectable = false
    obj.evented = false
  })

  const onMouseDown = (o) => {
    if (canvas.getActiveObject()) return
    isDrawing = true
    const pointer = canvas.getPointer(o.e)
    startX = pointer.x
    startY = pointer.y
    rect = new fabric.Rect({
      left: startX,
      top: startY,
      width: 0,
      height: 0,
      fill: 'transparent',
      stroke: color,
      strokeWidth,
      strokeUniform: true,
      selectable: true,
      evented: true,
      objectType: 'rectangle'
    })
    canvas.add(rect)
  }

  const onMouseMove = (o) => {
    if (!isDrawing || !rect) return
    const pointer = canvas.getPointer(o.e)
    const width = pointer.x - startX
    const height = pointer.y - startY

    rect.set({
      width: Math.abs(width),
      height: Math.abs(height),
      left: width < 0 ? pointer.x : startX,
      top: height < 0 ? pointer.y : startY
    })
    canvas.renderAll()
  }

  const onMouseUp = () => {
    if (!isDrawing) return
    isDrawing = false
    if (rect && (rect.width < 3 || rect.height < 3)) {
      canvas.remove(rect)
    } else if (rect) {
      rect.setCoords()
      canvas.setActiveObject(rect)
    }
    rect = null
    canvas.renderAll()
  }

  canvas.on('mouse:down', onMouseDown)
  canvas.on('mouse:move', onMouseMove)
  canvas.on('mouse:up', onMouseUp)

  return () => {
    canvas.off('mouse:down', onMouseDown)
    canvas.off('mouse:move', onMouseMove)
    canvas.off('mouse:up', onMouseUp)
    canvas.selection = true
    canvas.defaultCursor = 'default'
    canvas.forEachObject(obj => {
      obj.selectable = true
      obj.evented = true
    })
  }
}

// ---------------------------------------------------------------------------
// Tool 2: Circle / Ellipse
// ---------------------------------------------------------------------------

/**
 * Enable ellipse drawing tool on the canvas.
 * Click and drag to draw an ellipse.
 *
 * @param {fabric.Canvas} canvas - The Fabric.js canvas instance
 * @param {Object} options
 * @param {string} options.color - Stroke color (default '#ff3860')
 * @param {number} options.strokeWidth - Stroke width (default 2)
 * @returns {Function} Cleanup function to disable the tool
 */
export function enableCircleTool(canvas, options = {}) {
  const { color = '#ff3860', strokeWidth = 2 } = options
  let isDrawing = false
  let startX = 0
  let startY = 0
  let ellipse = null

  canvas.isDrawingMode = false
  canvas.selection = false
  canvas.defaultCursor = 'crosshair'
  canvas.forEachObject(obj => {
    obj.selectable = false
    obj.evented = false
  })

  const onMouseDown = (o) => {
    if (canvas.getActiveObject()) return
    isDrawing = true
    const pointer = canvas.getPointer(o.e)
    startX = pointer.x
    startY = pointer.y
    ellipse = new fabric.Ellipse({
      left: startX,
      top: startY,
      rx: 0,
      ry: 0,
      fill: 'transparent',
      stroke: color,
      strokeWidth,
      strokeUniform: true,
      selectable: true,
      evented: true,
      objectType: 'circle'
    })
    canvas.add(ellipse)
  }

  const onMouseMove = (o) => {
    if (!isDrawing || !ellipse) return
    const pointer = canvas.getPointer(o.e)
    const width = pointer.x - startX
    const height = pointer.y - startY

    ellipse.set({
      rx: Math.abs(width) / 2,
      ry: Math.abs(height) / 2,
      left: width < 0 ? pointer.x : startX,
      top: height < 0 ? pointer.y : startY
    })
    canvas.renderAll()
  }

  const onMouseUp = () => {
    if (!isDrawing) return
    isDrawing = false
    if (ellipse && (ellipse.rx < 3 || ellipse.ry < 3)) {
      canvas.remove(ellipse)
    } else if (ellipse) {
      ellipse.setCoords()
      canvas.setActiveObject(ellipse)
    }
    ellipse = null
    canvas.renderAll()
  }

  canvas.on('mouse:down', onMouseDown)
  canvas.on('mouse:move', onMouseMove)
  canvas.on('mouse:up', onMouseUp)

  return () => {
    canvas.off('mouse:down', onMouseDown)
    canvas.off('mouse:move', onMouseMove)
    canvas.off('mouse:up', onMouseUp)
    canvas.selection = true
    canvas.defaultCursor = 'default'
    canvas.forEachObject(obj => {
      obj.selectable = true
      obj.evented = true
    })
  }
}

// ---------------------------------------------------------------------------
// Tool 3: Arrow
// ---------------------------------------------------------------------------

/**
 * Build an arrow group from start and end coordinates.
 * Creates a fabric.Group containing a line and a triangular arrowhead.
 *
 * @param {number} startX
 * @param {number} startY
 * @param {number} endX
 * @param {number} endY
 * @param {Object} opts
 * @returns {fabric.Group}
 */
function buildArrowGroup(startX, startY, endX, endY, opts) {
  const { color = '#ff3860', strokeWidth = 2 } = opts
  const headLength = Math.max(10, strokeWidth * 5)
  const headWidth = Math.max(8, strokeWidth * 4)

  const angle =
    (Math.atan2(endY - startY, endX - startX) * 180) / Math.PI

  const line = new fabric.Line([startX, startY, endX, endY], {
    stroke: color,
    strokeWidth,
    strokeLineCap: 'round',
    selectable: false,
    evented: false
  })

  const arrowHead = new fabric.Triangle({
    left: endX,
    top: endY,
    originX: 'center',
    originY: 'center',
    width: headWidth,
    height: headLength,
    fill: color,
    angle: angle + 90,
    selectable: false,
    evented: false
  })

  const group = new fabric.Group([line, arrowHead], {
    selectable: true,
    evented: true,
    objectType: 'arrow'
  })

  return group
}

/**
 * Enable arrow drawing tool on the canvas.
 * Click to set start point, drag to aim, release to place arrow.
 *
 * @param {fabric.Canvas} canvas - The Fabric.js canvas instance
 * @param {Object} options
 * @param {string} options.color - Arrow color (default '#ff3860')
 * @param {number} options.strokeWidth - Line width (default 2)
 * @returns {Function} Cleanup function to disable the tool
 */
export function enableArrowTool(canvas, options = {}) {
  const { color = '#ff3860', strokeWidth = 2 } = options
  let isDrawing = false
  let startX = 0
  let startY = 0
  let tempLine = null

  canvas.isDrawingMode = false
  canvas.selection = false
  canvas.defaultCursor = 'crosshair'
  canvas.forEachObject(obj => {
    obj.selectable = false
    obj.evented = false
  })

  const onMouseDown = (o) => {
    if (canvas.getActiveObject()) return
    isDrawing = true
    const pointer = canvas.getPointer(o.e)
    startX = pointer.x
    startY = pointer.y
    tempLine = new fabric.Line([startX, startY, startX, startY], {
      stroke: color,
      strokeWidth,
      strokeDashArray: [4, 4],
      selectable: false,
      evented: false
    })
    canvas.add(tempLine)
  }

  const onMouseMove = (o) => {
    if (!isDrawing || !tempLine) return
    const pointer = canvas.getPointer(o.e)
    tempLine.set({ x2: pointer.x, y2: pointer.y })
    canvas.renderAll()
  }

  const onMouseUp = (o) => {
    if (!isDrawing) return
    isDrawing = false
    const pointer = canvas.getPointer(o.e)

    // Remove the temporary dashed line
    if (tempLine) {
      canvas.remove(tempLine)
      tempLine = null
    }

    // Only create arrow if dragged far enough
    const dx = pointer.x - startX
    const dy = pointer.y - startY
    const dist = Math.sqrt(dx * dx + dy * dy)
    if (dist < 10) {
      canvas.renderAll()
      return
    }

    const arrowGroup = buildArrowGroup(
      startX,
      startY,
      pointer.x,
      pointer.y,
      { color, strokeWidth }
    )
    canvas.add(arrowGroup)
    canvas.setActiveObject(arrowGroup)
    canvas.renderAll()
  }

  canvas.on('mouse:down', onMouseDown)
  canvas.on('mouse:move', onMouseMove)
  canvas.on('mouse:up', onMouseUp)

  return () => {
    canvas.off('mouse:down', onMouseDown)
    canvas.off('mouse:move', onMouseMove)
    canvas.off('mouse:up', onMouseUp)
    if (tempLine) {
      canvas.remove(tempLine)
      tempLine = null
    }
    canvas.selection = true
    canvas.defaultCursor = 'default'
    canvas.forEachObject(obj => {
      obj.selectable = true
      obj.evented = true
    })
  }
}

// ---------------------------------------------------------------------------
// Tool 4: Marker Point (numbered)
// ---------------------------------------------------------------------------

/**
 * Count existing marker objects on the canvas.
 *
 * @param {fabric.Canvas} canvas
 * @returns {number}
 */
function getExistingMarkerCount(canvas) {
  return canvas.getObjects().filter(o => o.objectType === 'marker').length
}

/**
 * Create a single numbered marker point on the canvas.
 *
 * @param {fabric.Canvas} canvas
 * @param {number} x - Center X coordinate
 * @param {number} y - Center Y coordinate
 * @param {number} number - Display number
 * @param {Object} options
 * @param {string} options.color - Marker fill color (default '#ff3860')
 * @param {number} options.size - Marker diameter (default 24)
 * @returns {fabric.Group}
 */
export function createMarkerPoint(canvas, x, y, number, options = {}) {
  const { color = '#ff3860', size = 24 } = options

  const circle = new fabric.Circle({
    radius: size / 2,
    fill: color,
    originX: 'center',
    originY: 'center',
    selectable: false,
    evented: false
  })

  const text = new fabric.Text(String(number), {
    fontSize: size * 0.55,
    fill: '#ffffff',
    fontFamily: 'Arial, sans-serif',
    fontWeight: 'bold',
    originX: 'center',
    originY: 'center',
    selectable: false,
    evented: false
  })

  const group = new fabric.Group([circle, text], {
    left: x - size / 2,
    top: y - size / 2,
    originX: 'left',
    originY: 'top',
    objectType: 'marker',
    markerNumber: number,
    selectable: true,
    evented: true
  })

  canvas.add(group)
  canvas.renderAll()
  return group
}

/**
 * Enable marker point tool on the canvas.
 * Each click places a numbered marker, auto-incrementing.
 *
 * @param {fabric.Canvas} canvas
 * @param {Object} options
 * @param {string} options.color - Marker fill color (default '#ff3860')
 * @param {number} options.size - Marker diameter (default 24)
 * @returns {Function} Cleanup function to disable the tool
 */
export function enableMarkerTool(canvas, options = {}) {
  let markerCount = getExistingMarkerCount(canvas)

  canvas.isDrawingMode = false
  canvas.selection = false
  canvas.defaultCursor = 'crosshair'
  canvas.forEachObject(obj => {
    obj.selectable = false
    obj.evented = false
  })

  const onClick = (o) => {
    // Avoid placing a marker when clicking an existing active object
    if (canvas.getActiveObject()) return
    const pointer = canvas.getPointer(o.e)
    markerCount++
    const marker = createMarkerPoint(
      canvas,
      pointer.x,
      pointer.y,
      markerCount,
      options
    )
    canvas.setActiveObject(marker)
  }

  canvas.on('mouse:down', onClick)

  return () => {
    canvas.off('mouse:down', onClick)
    canvas.selection = true
    canvas.defaultCursor = 'default'
    canvas.forEachObject(obj => {
      obj.selectable = true
      obj.evented = true
    })
  }
}

// ---------------------------------------------------------------------------
// Tool 5: Measurement
// ---------------------------------------------------------------------------

/**
 * Build a measurement group from two points.
 * Includes: a dashed line, two endpoint dots, and a distance label at midpoint.
 *
 * @param {number} x1
 * @param {number} y1
 * @param {number} x2
 * @param {number} y2
 * @param {Object} opts
 * @returns {fabric.Group}
 */
function buildMeasurementGroup(x1, y1, x2, y2, opts) {
  const { color = '#00b242', fontSize = 12 } = opts
  const dotRadius = 3

  const dx = x2 - x1
  const dy = y2 - y1
  const distance = Math.sqrt(dx * dx + dy * dy)

  const line = new fabric.Line([x1, y1, x2, y2], {
    stroke: color,
    strokeWidth: 1,
    strokeDashArray: [5, 3],
    selectable: false,
    evented: false
  })

  const dot1 = new fabric.Circle({
    left: x1 - dotRadius,
    top: y1 - dotRadius,
    radius: dotRadius,
    fill: color,
    selectable: false,
    evented: false
  })

  const dot2 = new fabric.Circle({
    left: x2 - dotRadius,
    top: y2 - dotRadius,
    radius: dotRadius,
    fill: color,
    selectable: false,
    evented: false
  })

  const midX = (x1 + x2) / 2
  const midY = (y1 + y2) / 2

  const label = new fabric.Text(`${Math.round(distance)}px`, {
    left: midX,
    top: midY - fontSize - 4,
    fontSize,
    fill: color,
    fontFamily: 'Arial, sans-serif',
    fontWeight: 'bold',
    backgroundColor: 'rgba(255,255,255,0.85)',
    padding: 2,
    selectable: false,
    evented: false
  })

  const group = new fabric.Group([line, dot1, dot2, label], {
    objectType: 'measurement',
    selectable: true,
    evented: true
  })

  return group
}

/**
 * Enable measurement tool on the canvas.
 * First click sets start point (shown as a dot), second click sets end point.
 * A dashed line with distance label is placed between the two points.
 *
 * @param {fabric.Canvas} canvas
 * @param {Object} options
 * @param {string} options.color - Line and label color (default '#00b242')
 * @param {number} options.fontSize - Label font size (default 12)
 * @returns {Function} Cleanup function to disable the tool
 */
export function enableMeasureTool(canvas, options = {}) {
  const { color = '#00b242', fontSize = 12 } = options
  let startPoint = null
  let startDot = null
  let tempLine = null

  canvas.isDrawingMode = false
  canvas.selection = false
  canvas.defaultCursor = 'crosshair'
  canvas.forEachObject(obj => {
    obj.selectable = false
    obj.evented = false
  })

  const onMouseDown = (o) => {
    const pointer = canvas.getPointer(o.e)

    if (!startPoint) {
      // First click: set start point and show a dot
      startPoint = { x: pointer.x, y: pointer.y }
      startDot = new fabric.Circle({
        left: pointer.x - 3,
        top: pointer.y - 3,
        radius: 3,
        fill: color,
        selectable: false,
        evented: false
      })
      canvas.add(startDot)
      canvas.renderAll()
    } else {
      // Second click: create measurement group
      // Remove temporary visuals
      if (startDot) {
        canvas.remove(startDot)
        startDot = null
      }
      if (tempLine) {
        canvas.remove(tempLine)
        tempLine = null
      }

      const group = buildMeasurementGroup(
        startPoint.x,
        startPoint.y,
        pointer.x,
        pointer.y,
        { color, fontSize }
      )
      canvas.add(group)
      canvas.setActiveObject(group)
      canvas.renderAll()
      startPoint = null
    }
  }

  const onMouseMove = (o) => {
    if (!startPoint) return
    const pointer = canvas.getPointer(o.e)

    // Show a live preview line from start to cursor
    if (tempLine) {
      canvas.remove(tempLine)
    }
    tempLine = new fabric.Line(
      [startPoint.x, startPoint.y, pointer.x, pointer.y],
      {
        stroke: color,
        strokeWidth: 1,
        strokeDashArray: [5, 3],
        selectable: false,
        evented: false
      }
    )
    canvas.add(tempLine)
    canvas.renderAll()
  }

  canvas.on('mouse:down', onMouseDown)
  canvas.on('mouse:move', onMouseMove)

  return () => {
    canvas.off('mouse:down', onMouseDown)
    canvas.off('mouse:move', onMouseMove)
    if (startDot) {
      canvas.remove(startDot)
      startDot = null
    }
    if (tempLine) {
      canvas.remove(tempLine)
      tempLine = null
    }
    startPoint = null
    canvas.selection = true
    canvas.defaultCursor = 'default'
    canvas.forEachObject(obj => {
      obj.selectable = true
      obj.evented = true
    })
  }
}

// ---------------------------------------------------------------------------
// Utility: Disable all custom tools
// ---------------------------------------------------------------------------

/**
 * Reset canvas to default selection mode.
 * Does NOT remove event handlers — each tool's cleanup function does that.
 *
 * @param {fabric.Canvas} canvas
 */
export function disableAllTools(canvas) {
  canvas.isDrawingMode = false
  canvas.selection = true
  canvas.defaultCursor = 'default'
  canvas.forEachObject(obj => {
    obj.selectable = true
    obj.evented = true
  })
}

// ---------------------------------------------------------------------------
// Serialization helpers
// ---------------------------------------------------------------------------

/**
 * Custom properties that need to be included when serializing objects
 * created by these tools. Pass to fabric's toJSON / toObject calls.
 */
export const CUSTOM_PROPERTIES = [
  'objectType',
  'markerNumber',
  'id',
  'canvasWidth',
  'canvasHeight',
  'createdBy'
]

/**
 * Get all tool-created objects from the canvas, grouped by type.
 *
 * @param {fabric.Canvas} canvas
 * @returns {Object} Map of objectType -> array of fabric objects
 */
export function getToolObjects(canvas) {
  const result = {
    rectangle: [],
    circle: [],
    arrow: [],
    marker: [],
    measurement: []
  }
  canvas.getObjects().forEach(obj => {
    if (obj.objectType && result[obj.objectType]) {
      result[obj.objectType].push(obj)
    }
  })
  return result
}
