<template>
  <div
    ref="container"
    class="asset-force-graph"
    :style="{ height: height + 'px' }"
  >
    <div class="graph-loading" v-if="loading">
      <span>加载图谱引擎...</span>
    </div>
    <div class="graph-controls" v-if="!loading">
      <button class="graph-btn" @click="zoomIn" title="放大">+</button>
      <button class="graph-btn" @click="zoomOut" title="缩小">−</button>
      <button class="graph-btn" @click="resetZoom" title="重置">⟲</button>
      <button class="graph-btn" @click="toggleLabels" title="标签">
        {{ labelsVisible ? 'Aa' : 'A̶a̶' }}
      </button>
    </div>
    <div
      ref="tooltip"
      class="graph-tooltip"
      :class="{ visible: tooltip.show }"
      :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px' }"
    >
      <div class="tooltip-title">{{ tooltip.title }}</div>
      <div class="tooltip-meta" v-if="tooltip.meta">{{ tooltip.meta }}</div>
    </div>
    <svg
      ref="svg"
      class="graph-svg"
      v-show="!loading && usesSvg"
    ></svg>
    <canvas
      ref="canvas"
      class="graph-canvas"
      v-show="!loading && !usesSvg"
    ></canvas>
  </div>
</template>

<script>
import {
  getNodeColor,
  getNodeSize,
  getLinkDashArray,
  linkHasArrow,
  getLinkOpacity,
  getLinkWidth,
  hexagonPath,
  diamondPath,
  NODE_SHAPES,
  NODE_LABELS,
  LINK_LABELS
} from '@/lib/graph-utils.js'

let d3 = null

export default {
  name: 'asset-force-graph',

  props: {
    graphData: {
      type: Object,
      default: () => ({ nodes: [], links: [] })
    },
    width: {
      type: Number,
      default: 0
    },
    height: {
      type: Number,
      default: 600
    },
    centerNodeId: {
      type: String,
      default: null
    },
    interactive: {
      type: Boolean,
      default: true
    },
    showLabels: {
      type: Boolean,
      default: true
    }
  },

  emits: ['node-click', 'node-dblclick', 'link-click', 'node-drag-end'],

  data() {
    return {
      loading: true,
      labelsVisible: this.showLabels,
      tooltip: { show: false, x: 0, y: 0, title: '', meta: '' },
      simulation: null,
      zoomBehavior: null,
      resizeObserver: null,
      containerWidth: 0,
      highlightedNodeId: null
    }
  },

  computed: {
    effectiveWidth() {
      return this.width || this.containerWidth || 800
    },

    usesSvg() {
      if (!this.graphData || !this.graphData.nodes) return true
      return this.graphData.nodes.length <= 500
    }
  },

  async mounted() {
    await this.loadD3()
    this.setupResizeObserver()
    this.initGraph()
  },

  beforeUnmount() {
    this.destroyGraph()
    if (this.resizeObserver) {
      this.resizeObserver.disconnect()
    }
  },

  watch: {
    graphData: {
      deep: true,
      handler() {
        this.initGraph()
      }
    },
    centerNodeId() {
      this.updateHighlight()
    },
    showLabels(val) {
      this.labelsVisible = val
    }
  },

  methods: {
    async loadD3() {
      if (d3) {
        this.loading = false
        return
      }
      try {
        d3 = await import('https://cdn.jsdelivr.net/npm/d3@7/+esm')
      } catch {
        // Fallback CDN
        try {
          d3 = await import('https://unpkg.com/d3@7/+esm')
        } catch (err) {
          console.error('Failed to load D3.js:', err)
        }
      }
      this.loading = false
    },

    setupResizeObserver() {
      if (!this.$refs.container) return
      this.resizeObserver = new ResizeObserver((entries) => {
        for (const entry of entries) {
          this.containerWidth = entry.contentRect.width
        }
      })
      this.resizeObserver.observe(this.$refs.container)
      this.containerWidth = this.$refs.container.clientWidth
    },

    initGraph() {
      if (!d3 || this.loading) return
      this.destroyGraph()

      const nodes = this.graphData.nodes || []
      const links = this.graphData.links || []
      if (!nodes.length) return

      if (this.usesSvg) {
        this.initSvgGraph(nodes, links)
      } else {
        this.initCanvasGraph(nodes, links)
      }
    },

    destroyGraph() {
      if (this.simulation) {
        this.simulation.stop()
        this.simulation = null
      }
      if (this.$refs.svg) {
        d3.select(this.$refs.svg).selectAll('*').remove()
      }
    },

    // ========== SVG Rendering ==========

    initSvgGraph(nodesData, linksData) {
      const svg = d3.select(this.$refs.svg)
      const w = this.effectiveWidth
      const h = this.height

      svg.attr('width', w).attr('height', h).attr('viewBox', `0 0 ${w} ${h}`)

      // Defs: arrow markers and glow filter
      const defs = svg.append('defs')

      defs
        .append('marker')
        .attr('id', 'arrowhead')
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 28)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', 'var(--text-alt, #999)')

      const glowFilter = defs.append('filter').attr('id', 'glow')
      glowFilter
        .append('feGaussianBlur')
        .attr('stdDeviation', '3')
        .attr('result', 'blur')
      const feMerge = glowFilter.append('feMerge')
      feMerge.append('feMergeNode').attr('in', 'blur')
      feMerge.append('feMergeNode').attr('in', 'SourceGraphic')

      // Container group for zoom/pan
      const g = svg.append('g').attr('class', 'graph-root')

      // Setup zoom
      this.zoomBehavior = d3
        .zoom()
        .scaleExtent([0.1, 4])
        .on('zoom', (event) => {
          g.attr('transform', event.transform)
        })

      if (this.interactive) {
        svg.call(this.zoomBehavior)
      }

      // Deep-clone data for d3 mutation
      const nodes = nodesData.map((n) => ({ ...n }))
      const links = linksData.map((l) => ({
        ...l,
        source: l.source_id || l.source,
        target: l.target_id || l.target
      }))

      // Force simulation
      this.simulation = d3
        .forceSimulation(nodes)
        .force(
          'link',
          d3
            .forceLink(links)
            .id((d) => d.id)
            .distance((d) => {
              const weight = d.weight || 1
              return Math.max(40, 150 / weight)
            })
        )
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(w / 2, h / 2))
        .force('collide', d3.forceCollide().radius(30))
        .alphaDecay(0.02)

      // Draw links
      const linkGroup = g
        .append('g')
        .attr('class', 'links')
        .selectAll('line')
        .data(links)
        .join('line')
        .attr('stroke', 'var(--text-alt, #666)')
        .attr('stroke-opacity', (d) => getLinkOpacity(d.link_type))
        .attr('stroke-width', (d) => getLinkWidth(d.weight))
        .attr('stroke-dasharray', (d) => getLinkDashArray(d.link_type))
        .attr('marker-end', (d) =>
          linkHasArrow(d.link_type) ? 'url(#arrowhead)' : null
        )
        .on('mouseenter', (event, d) => {
          this.showTooltip(
            event,
            LINK_LABELS[d.link_type] || d.link_type,
            `权重: ${(d.weight || 1).toFixed(2)}`
          )
        })
        .on('mouseleave', () => this.hideTooltip())
        .on('click', (event, d) => {
          event.stopPropagation()
          this.$emit('link-click', d)
        })

      // Draw nodes
      const nodeGroup = g
        .append('g')
        .attr('class', 'nodes')
        .selectAll('g')
        .data(nodes)
        .join('g')
        .attr('class', 'node-group')
        .attr('cursor', 'pointer')
        .on('mouseenter', (event, d) => {
          const typeLabel = NODE_LABELS[d.node_type] || d.node_type
          this.showTooltip(event, d.name || d.label || d.id, typeLabel)
        })
        .on('mouseleave', () => this.hideTooltip())
        .on('click', (event, d) => {
          event.stopPropagation()
          this.onNodeClick(d)
        })
        .on('dblclick', (event, d) => {
          event.stopPropagation()
          this.$emit('node-dblclick', d)
        })

      // Add drag behavior
      if (this.interactive) {
        nodeGroup.call(this.createDragBehavior())
      }

      // Render node shapes
      nodeGroup.each((d, i, nodeElements) => {
        const el = d3.select(nodeElements[i])
        const isCenterNode = d.id === this.centerNodeId
        const size = getNodeSize(d, isCenterNode)
        const color = getNodeColor(d)
        const shape = NODE_SHAPES[d.node_type] || 'circle'

        if (isCenterNode) {
          el.attr('filter', 'url(#glow)')
        }

        switch (shape) {
          case 'circle':
            el.append('circle')
              .attr('r', size)
              .attr('fill', color)
              .attr('stroke', isCenterNode ? '#fff' : 'none')
              .attr('stroke-width', isCenterNode ? 2 : 0)
            break
          case 'circle-sm':
            el.append('circle')
              .attr('r', size)
              .attr('fill', color)
            break
          case 'rect':
            el.append('rect')
              .attr('x', -size / 2)
              .attr('y', -size / 2)
              .attr('width', size)
              .attr('height', size)
              .attr('rx', 3)
              .attr('fill', color)
              .attr('stroke', isCenterNode ? '#fff' : 'none')
              .attr('stroke-width', isCenterNode ? 2 : 0)
            break
          case 'diamond':
            el.append('polygon')
              .attr('points', diamondPath(size))
              .attr('fill', color)
              .attr('stroke', isCenterNode ? '#fff' : 'none')
              .attr('stroke-width', isCenterNode ? 2 : 0)
            break
          case 'hexagon':
            el.append('polygon')
              .attr('points', hexagonPath(size))
              .attr('fill', color)
              .attr('stroke', isCenterNode ? '#fff' : 'none')
              .attr('stroke-width', isCenterNode ? 2 : 0)
            break
          case 'rounded-rect':
            el.append('rect')
              .attr('x', -size * 0.7)
              .attr('y', -size * 0.4)
              .attr('width', size * 1.4)
              .attr('height', size * 0.8)
              .attr('rx', size * 0.2)
              .attr('fill', color)
              .attr('stroke', isCenterNode ? '#fff' : 'none')
              .attr('stroke-width', isCenterNode ? 2 : 0)
            break
        }
      })

      // Render labels
      nodeGroup
        .append('text')
        .attr('class', 'node-label')
        .attr('dy', (d) => {
          const size = getNodeSize(d, d.id === this.centerNodeId)
          return size + 14
        })
        .attr('text-anchor', 'middle')
        .attr('fill', 'var(--text, #eee)')
        .attr('font-size', '11px')
        .attr('pointer-events', 'none')
        .attr('opacity', this.labelsVisible ? 1 : 0)
        .text((d) => {
          const name = d.name || d.label || d.id
          return name.length > 10 ? name.slice(0, 10) + '...' : name
        })

      // Click on background to deselect
      svg.on('click', () => {
        this.highlightedNodeId = null
        this.updateNodeOpacity(nodeGroup, linkGroup, null)
      })

      // Tick handler
      this.simulation.on('tick', () => {
        linkGroup
          .attr('x1', (d) => d.source.x)
          .attr('y1', (d) => d.source.y)
          .attr('x2', (d) => d.target.x)
          .attr('y2', (d) => d.target.y)

        nodeGroup.attr('transform', (d) => `translate(${d.x},${d.y})`)
      })

      // Apply initial highlight
      this.updateHighlight()
    },

    // ========== Canvas Rendering (>500 nodes) ==========

    initCanvasGraph(nodesData, linksData) {
      const canvas = this.$refs.canvas
      const w = this.effectiveWidth
      const h = this.height
      const dpr = window.devicePixelRatio || 1

      canvas.width = w * dpr
      canvas.height = h * dpr
      canvas.style.width = w + 'px'
      canvas.style.height = h + 'px'

      const ctx = canvas.getContext('2d')
      ctx.scale(dpr, dpr)

      const nodes = nodesData.map((n) => ({ ...n }))
      const links = linksData.map((l) => ({
        ...l,
        source: l.source_id || l.source,
        target: l.target_id || l.target
      }))

      let transform = d3.zoomIdentity

      this.simulation = d3
        .forceSimulation(nodes)
        .force(
          'link',
          d3
            .forceLink(links)
            .id((d) => d.id)
            .distance((d) => Math.max(40, 150 / (d.weight || 1)))
        )
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(w / 2, h / 2))
        .force('collide', d3.forceCollide().radius(30))
        .alphaDecay(0.02)

      const drawFrame = () => {
        ctx.save()
        ctx.clearRect(0, 0, w, h)
        ctx.translate(transform.x, transform.y)
        ctx.scale(transform.k, transform.k)

        // Draw links
        links.forEach((l) => {
          if (!l.source.x || !l.target.x) return
          ctx.beginPath()
          ctx.moveTo(l.source.x, l.source.y)
          ctx.lineTo(l.target.x, l.target.y)
          ctx.strokeStyle = 'rgba(150,150,150,' + getLinkOpacity(l.link_type) + ')'
          ctx.lineWidth = getLinkWidth(l.weight)
          ctx.stroke()
        })

        // Draw nodes
        nodes.forEach((n) => {
          if (!n.x) return
          const isCenterNode = n.id === this.centerNodeId
          const size = getNodeSize(n, isCenterNode)
          const color = getNodeColor(n)

          ctx.beginPath()
          ctx.arc(n.x, n.y, size, 0, 2 * Math.PI)
          ctx.fillStyle = color
          ctx.fill()

          if (isCenterNode) {
            ctx.strokeStyle = '#fff'
            ctx.lineWidth = 2
            ctx.stroke()
          }

          // Label
          if (this.labelsVisible) {
            ctx.fillStyle = '#ccc'
            ctx.font = '10px sans-serif'
            ctx.textAlign = 'center'
            const name = n.name || n.label || n.id
            const label = name.length > 10 ? name.slice(0, 10) + '...' : name
            ctx.fillText(label, n.x, n.y + size + 12)
          }
        })

        ctx.restore()
      }

      this.simulation.on('tick', drawFrame)

      // Canvas zoom
      if (this.interactive) {
        this.zoomBehavior = d3
          .zoom()
          .scaleExtent([0.1, 4])
          .on('zoom', (event) => {
            transform = event.transform
            drawFrame()
          })

        d3.select(canvas).call(this.zoomBehavior)

        // Canvas drag support
        d3.select(canvas).on('mousedown.drag', (event) => {
          const [mx, my] = d3.pointer(event)
          const x = (mx - transform.x) / transform.k
          const y = (my - transform.y) / transform.k
          const node = this.findClosestNode(nodes, x, y)
          if (!node) return

          event.preventDefault()
          const onMouseMove = (e) => {
            const [px, py] = d3.pointer(e, canvas)
            node.fx = (px - transform.x) / transform.k
            node.fy = (py - transform.y) / transform.k
            this.simulation.alpha(0.3).restart()
          }
          const onMouseUp = () => {
            document.removeEventListener('mousemove', onMouseMove)
            document.removeEventListener('mouseup', onMouseUp)
            node.fx = null
            node.fy = null
            this.$emit('node-drag-end', node)
          }
          document.addEventListener('mousemove', onMouseMove)
          document.addEventListener('mouseup', onMouseUp)
        })

        // Canvas click
        d3.select(canvas).on('click.graph', (event) => {
          const [mx, my] = d3.pointer(event)
          const x = (mx - transform.x) / transform.k
          const y = (my - transform.y) / transform.k
          const node = this.findClosestNode(nodes, x, y)
          if (node) {
            this.$emit('node-click', node)
          }
        })

        d3.select(canvas).on('dblclick.graph', (event) => {
          const [mx, my] = d3.pointer(event)
          const x = (mx - transform.x) / transform.k
          const y = (my - transform.y) / transform.k
          const node = this.findClosestNode(nodes, x, y)
          if (node) {
            this.$emit('node-dblclick', node)
          }
        })
      }
    },

    findClosestNode(nodes, x, y) {
      let closest = null
      let minDist = Infinity
      for (const n of nodes) {
        if (!n.x) continue
        const dx = n.x - x
        const dy = n.y - y
        const dist = dx * dx + dy * dy
        const size = getNodeSize(n, n.id === this.centerNodeId)
        if (dist < size * size && dist < minDist) {
          minDist = dist
          closest = n
        }
      }
      return closest
    },

    // ========== Drag Behavior (SVG) ==========

    createDragBehavior() {
      return d3
        .drag()
        .on('start', (event, d) => {
          if (!event.active) this.simulation.alphaTarget(0.3).restart()
          d.fx = d.x
          d.fy = d.y
        })
        .on('drag', (event, d) => {
          d.fx = event.x
          d.fy = event.y
        })
        .on('end', (event, d) => {
          if (!event.active) this.simulation.alphaTarget(0)
          d.fx = null
          d.fy = null
          this.$emit('node-drag-end', d)
        })
    },

    // ========== Interaction Helpers ==========

    onNodeClick(node) {
      this.highlightedNodeId =
        this.highlightedNodeId === node.id ? null : node.id
      this.$emit('node-click', node)

      // Update highlight in SVG mode
      if (this.usesSvg && this.$refs.svg) {
        const svg = d3.select(this.$refs.svg)
        const nodeGroup = svg.selectAll('.node-group')
        const linkGroup = svg.selectAll('.links line')
        this.updateNodeOpacity(nodeGroup, linkGroup, this.highlightedNodeId)
      }
    },

    updateNodeOpacity(nodeGroup, linkGroup, highlightId) {
      if (!nodeGroup || !d3) return

      if (!highlightId) {
        nodeGroup.attr('opacity', 1)
        linkGroup.attr('opacity', (d) => getLinkOpacity(d.link_type))
        return
      }

      // Get connected node ids
      const connectedIds = new Set([highlightId])
      linkGroup.each((d) => {
        const sourceId = typeof d.source === 'object' ? d.source.id : d.source
        const targetId = typeof d.target === 'object' ? d.target.id : d.target
        if (sourceId === highlightId) connectedIds.add(targetId)
        if (targetId === highlightId) connectedIds.add(sourceId)
      })

      nodeGroup.attr('opacity', (d) => (connectedIds.has(d.id) ? 1 : 0.15))

      linkGroup.attr('opacity', (d) => {
        const sourceId = typeof d.source === 'object' ? d.source.id : d.source
        const targetId = typeof d.target === 'object' ? d.target.id : d.target
        if (sourceId === highlightId || targetId === highlightId) {
          return getLinkOpacity(d.link_type)
        }
        return 0.05
      })
    },

    updateHighlight() {
      if (!this.usesSvg || !this.$refs.svg || !d3) return
      const svg = d3.select(this.$refs.svg)
      const nodeGroup = svg.selectAll('.node-group')
      const linkGroup = svg.selectAll('.links line')
      if (this.centerNodeId) {
        this.highlightedNodeId = this.centerNodeId
        this.updateNodeOpacity(nodeGroup, linkGroup, this.centerNodeId)
      }
    },

    showTooltip(event, title, meta) {
      const rect = this.$refs.container.getBoundingClientRect()
      this.tooltip = {
        show: true,
        x: event.clientX - rect.left + 12,
        y: event.clientY - rect.top - 8,
        title: title || '',
        meta: meta || ''
      }
    },

    hideTooltip() {
      this.tooltip.show = false
    },

    toggleLabels() {
      this.labelsVisible = !this.labelsVisible
      if (this.usesSvg && this.$refs.svg) {
        d3.select(this.$refs.svg)
          .selectAll('.node-label')
          .attr('opacity', this.labelsVisible ? 1 : 0)
      }
    },

    // ========== Zoom Controls ==========

    zoomIn() {
      if (!this.zoomBehavior || !d3) return
      const target = this.usesSvg
        ? d3.select(this.$refs.svg)
        : d3.select(this.$refs.canvas)
      target.transition().duration(300).call(this.zoomBehavior.scaleBy, 1.3)
    },

    zoomOut() {
      if (!this.zoomBehavior || !d3) return
      const target = this.usesSvg
        ? d3.select(this.$refs.svg)
        : d3.select(this.$refs.canvas)
      target.transition().duration(300).call(this.zoomBehavior.scaleBy, 0.7)
    },

    resetZoom() {
      if (!this.zoomBehavior || !d3) return
      const target = this.usesSvg
        ? d3.select(this.$refs.svg)
        : d3.select(this.$refs.canvas)
      target
        .transition()
        .duration(500)
        .call(this.zoomBehavior.transform, d3.zoomIdentity)
    }
  }
}
</script>

<style lang="scss" scoped>
.asset-force-graph {
  position: relative;
  width: 100%;
  overflow: hidden;
  border-radius: 0.8em;
  border: 1px solid var(--border);
  background: var(--background);
}

.graph-svg,
.graph-canvas {
  display: block;
  width: 100%;
  height: 100%;
}

.graph-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-alt);
  font-size: 0.9em;
}

.graph-controls {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  z-index: 10;
}

.graph-btn {
  width: 30px;
  height: 30px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--background);
  color: var(--text);
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;

  &:hover {
    background: var(--background-hover, var(--background-selectable));
  }
}

.graph-tooltip {
  position: absolute;
  pointer-events: none;
  z-index: 20;
  background: rgba(0, 0, 0, 0.85);
  color: #fff;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 12px;
  white-space: nowrap;
  opacity: 0;
  transition: opacity 0.15s;

  &.visible {
    opacity: 1;
  }
}

.tooltip-title {
  font-weight: 600;
}

.tooltip-meta {
  font-size: 11px;
  color: #aaa;
  margin-top: 2px;
}
</style>
