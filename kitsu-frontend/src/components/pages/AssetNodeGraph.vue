<template>
  <page-layout :side="!!selectedNode">
    <template #main>
      <div class="asset-node-graph">
        <header class="flexrow">
          <page-title class="mt1 filler" text="资产图谱" />
        </header>

        <!-- Toolbar -->
        <div class="toolbar flexrow">
          <div class="toolbar-group flexrow">
            <span class="toolbar-label">视图</span>
            <button-simple
              :class="{ active: graphViewMode === 'global' }"
              text="全局"
              @click="switchView('global')"
            />
            <button-simple
              :class="{ active: graphViewMode === 'asset' }"
              text="资产"
              @click="switchView('asset')"
            />
            <button-simple
              :class="{ active: graphViewMode === 'project' }"
              text="项目"
              @click="switchView('project')"
            />
          </div>

          <div class="toolbar-group flexrow">
            <span class="toolbar-label">深度</span>
            <button-simple
              v-for="d in [1, 2, 3]"
              :key="d"
              :class="{ active: graphDepth === d }"
              :text="String(d)"
              @click="onDepthChange(d)"
            />
          </div>

          <div class="toolbar-group flexrow">
            <span class="toolbar-label">筛选</span>
            <combobox-multi
              class="filter-combo"
              placeholder="节点类型"
              :options="nodeTypeOptions"
              v-model="localFilterNodeTypes"
              @change="onFilterChange"
            />
            <combobox-multi
              class="filter-combo"
              placeholder="边类型"
              :options="linkTypeOptions"
              v-model="localFilterLinkTypes"
              @change="onFilterChange"
            />
          </div>

          <span class="filler"></span>

          <div class="toolbar-group flexrow">
            <button-simple
              icon="bar-chart-2"
              :text="showStats ? '隐藏统计' : '统计'"
              @click="showStats = !showStats"
            />
            <button-simple
              icon="refresh-cw"
              text="刷新"
              @click="refreshGraph"
            />
          </div>
        </div>

        <!-- Main content area -->
        <div class="graph-container flexrow">
          <!-- Stats panel -->
          <div class="stats-panel" v-if="showStats">
            <h3>图谱统计</h3>
            <div class="stat-row">
              <span class="stat-label">节点总数</span>
              <span class="stat-value">{{ nodeCount }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">边总数</span>
              <span class="stat-value">{{ linkCount }}</span>
            </div>

            <div class="stat-section" v-if="Object.keys(nodesByType).length">
              <h4>节点类型分布</h4>
              <div
                class="stat-bar-row"
                v-for="(nodes, type) in nodesByType"
                :key="'nt-' + type"
              >
                <span class="stat-bar-label">{{ getNodeTypeLabel(type) }}</span>
                <div class="stat-bar-track">
                  <div
                    class="stat-bar-fill"
                    :style="{
                      width: nodeCount ? (nodes.length / nodeCount * 100) + '%' : '0%',
                      backgroundColor: getNodeTypeColor(type)
                    }"
                  ></div>
                </div>
                <span class="stat-bar-count">{{ nodes.length }}</span>
              </div>
            </div>

            <div class="stat-section" v-if="Object.keys(linksByType).length">
              <h4>边类型分布</h4>
              <div
                class="stat-bar-row"
                v-for="(links, type) in linksByType"
                :key="'lt-' + type"
              >
                <span class="stat-bar-label">{{ getLinkTypeLabel(type) }}</span>
                <div class="stat-bar-track">
                  <div
                    class="stat-bar-fill"
                    :style="{
                      width: linkCount ? (links.length / linkCount * 100) + '%' : '0%',
                      backgroundColor: getLinkTypeColor(type)
                    }"
                  ></div>
                </div>
                <span class="stat-bar-count">{{ links.length }}</span>
              </div>
            </div>
          </div>

          <!-- D3 Force Graph area -->
          <div class="graph-viewport filler" ref="graphViewport">
            <table-info
              :is-loading="isGraphLoading"
              v-if="isGraphLoading"
            />
            <div
              class="has-text-centered empty-message"
              v-else-if="!nodeCount"
            >
              暂无图谱数据
            </div>
            <svg
              ref="graphSvg"
              class="graph-svg"
              v-show="nodeCount > 0 && !isGraphLoading"
            ></svg>
          </div>
        </div>
      </div>
    </template>

    <template #side>
      <div class="node-detail-panel" v-if="selectedNode">
        <div class="panel-header flexrow">
          <h2 class="filler">节点详情</h2>
          <button-simple
            icon="x"
            @click="clearSelection"
          />
        </div>

        <!-- Node basic info -->
        <div class="panel-section">
          <h3>基本信息</h3>
          <div class="info-row">
            <span class="info-label">标签</span>
            <span class="info-value">{{ selectedNode.label || selectedNode.name }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">类型</span>
            <span class="info-value">
              <span
                class="node-type-dot"
                :style="{ backgroundColor: getNodeTypeColor(selectedNode.node_type) }"
              ></span>
              {{ getNodeTypeLabel(selectedNode.node_type) }}
            </span>
          </div>
          <div class="info-row" v-if="selectedNode.global_asset_id">
            <span class="info-label">资产ID</span>
            <span class="info-value">{{ selectedNode.global_asset_id }}</span>
          </div>
          <div class="info-row" v-if="selectedNode.metadata">
            <span class="info-label">元数据</span>
            <span class="info-value metadata-value">
              {{ JSON.stringify(selectedNode.metadata, null, 2) }}
            </span>
          </div>
        </div>

        <!-- Connected links -->
        <div class="panel-section" v-if="selectedNodeLinksList.length">
          <h3>关联列表 ({{ selectedNodeLinksList.length }})</h3>
          <ul class="link-list">
            <li
              v-for="link in selectedNodeLinksList"
              :key="link.id"
              class="link-item flexrow"
            >
              <span
                class="link-type-badge"
                :style="{ backgroundColor: getLinkTypeColor(link.link_type) }"
              >
                {{ getLinkTypeLabel(link.link_type) }}
              </span>
              <span class="link-target filler">
                {{ getLinkedNodeLabel(link) }}
              </span>
              <button-simple
                class="link-delete-btn"
                icon="x"
                @click="onDeleteLink(link.id)"
                v-if="isCurrentUserManager"
              />
            </li>
          </ul>
        </div>

        <!-- Actions -->
        <div class="panel-actions">
          <button-simple
            text="查看资产详情"
            icon="external-link"
            @click="goToAssetDetail"
            v-if="selectedNode.global_asset_id"
          />
          <button-simple
            text="自动关联"
            icon="zap"
            @click="onAutoLink"
            v-if="selectedNode.global_asset_id && isCurrentUserManager"
          />
          <button-simple
            text="手动添加关联"
            icon="plus"
            @click="showAddLinkModal = true"
            v-if="isCurrentUserManager"
          />
        </div>
      </div>
    </template>
  </page-layout>
</template>

<script>
import * as d3 from 'd3'
import { mapGetters, mapActions } from 'vuex'

import ButtonSimple from '@/components/widgets/ButtonSimple.vue'
import Combobox from '@/components/widgets/Combobox.vue'
import PageLayout from '@/components/layouts/PageLayout.vue'
import PageTitle from '@/components/widgets/PageTitle.vue'
import TableInfo from '@/components/widgets/TableInfo.vue'

const NODE_TYPE_LABELS = {
  asset: '资产',
  character: '人物',
  scene: '场景',
  prop: '道具',
  effect: '特效',
  music: '音乐',
  prompt: '提示词',
  style: '风格',
  camera_language: '镜头语言',
  project: '项目',
  tag: '标签'
}

const NODE_TYPE_COLORS = {
  asset: '#6366f1',
  character: '#f59e0b',
  scene: '#10b981',
  prop: '#8b5cf6',
  effect: '#ef4444',
  music: '#ec4899',
  prompt: '#06b6d4',
  style: '#f97316',
  camera_language: '#84cc16',
  project: '#3b82f6',
  tag: '#a1a1aa'
}

const LINK_TYPE_LABELS = {
  same_tag: '同标签',
  same_style: '同风格',
  same_project: '同项目',
  derived_from: '衍生自',
  variant_of: '变体',
  used_in: '用于',
  references: '引用',
  manual: '手动关联'
}

const LINK_TYPE_COLORS = {
  same_tag: '#a1a1aa',
  same_style: '#f59e0b',
  same_project: '#3b82f6',
  derived_from: '#10b981',
  variant_of: '#8b5cf6',
  used_in: '#ef4444',
  references: '#06b6d4',
  manual: '#ec4899'
}

// ComboboxMulti stub — uses regular Combobox if ComboboxMulti is not available
const ComboboxMulti = {
  name: 'combobox-multi',
  props: {
    options: { type: Array, default: () => [] },
    modelValue: { type: Array, default: () => [] },
    placeholder: { type: String, default: '' }
  },
  emits: ['update:modelValue', 'change'],
  data() {
    return { internalValue: '' }
  },
  methods: {
    onChange(val) {
      if (!val) return
      const current = [...(this.modelValue || [])]
      const idx = current.indexOf(val)
      if (idx >= 0) {
        current.splice(idx, 1)
      } else {
        current.push(val)
      }
      this.$emit('update:modelValue', current)
      this.$emit('change', current)
      this.internalValue = ''
    }
  },
  render() {
    const h = this.$createElement || ((...args) => {
      // Vue 3 fallback
      return null
    })
    // We render using the Combobox component via template below
    return null
  },
  template: `
    <div class="combobox-multi-wrapper">
      <select
        class="combobox-multi-select"
        v-model="internalValue"
        @change="onChange(internalValue)"
      >
        <option value="" disabled>{{ placeholder }}</option>
        <option
          v-for="opt in options"
          :key="opt.value"
          :value="opt.value"
        >
          {{ modelValue.includes(opt.value) ? '✓ ' : '' }}{{ opt.label }}
        </option>
      </select>
      <div class="combobox-multi-tags" v-if="modelValue.length">
        <span
          class="multi-tag"
          v-for="val in modelValue"
          :key="val"
          @click="onChange(val)"
        >
          {{ (options.find(o => o.value === val) || {}).label || val }}
          <span class="multi-tag-x">&times;</span>
        </span>
      </div>
    </div>
  `
}

export default {
  name: 'asset-node-graph',

  components: {
    ButtonSimple,
    Combobox,
    ComboboxMulti,
    PageLayout,
    PageTitle,
    TableInfo
  },

  data() {
    return {
      showStats: false,
      showAddLinkModal: false,
      localFilterNodeTypes: [],
      localFilterLinkTypes: [],
      simulation: null,
      svgGroup: null,
      zoom: null
    }
  },

  mounted() {
    this.loadGlobalGraph()
    this.loadGraphStats()
    this.$nextTick(() => {
      this.initGraph()
    })
  },

  beforeUnmount() {
    if (this.simulation) {
      this.simulation.stop()
    }
  },

  computed: {
    ...mapGetters([
      'assetGraphData',
      'assetGraphStats',
      'assetGraphSelectedNode',
      'assetGraphDepth',
      'isAssetGraphLoading',
      'assetGraphViewMode',
      'assetGraphNodeCount',
      'assetGraphLinkCount',
      'assetGraphNodesByType',
      'assetGraphLinksByType',
      'selectedNodeLinks',
      'isCurrentUserAdmin',
      'isCurrentUserManager'
    ]),

    selectedNode() {
      return this.assetGraphSelectedNode
    },

    graphViewMode() {
      return this.assetGraphViewMode
    },

    graphDepth() {
      return this.assetGraphDepth
    },

    isGraphLoading() {
      return this.isAssetGraphLoading
    },

    nodeCount() {
      return this.assetGraphNodeCount
    },

    linkCount() {
      return this.assetGraphLinkCount
    },

    nodesByType() {
      return this.assetGraphNodesByType
    },

    linksByType() {
      return this.assetGraphLinksByType
    },

    selectedNodeLinksList() {
      return this.selectedNodeLinks
    },

    nodeTypeOptions() {
      return Object.entries(NODE_TYPE_LABELS).map(([value, label]) => ({
        value,
        label
      }))
    },

    linkTypeOptions() {
      return Object.entries(LINK_TYPE_LABELS).map(([value, label]) => ({
        value,
        label
      }))
    }
  },

  watch: {
    assetGraphData: {
      handler() {
        this.$nextTick(() => {
          this.renderGraph()
        })
      },
      deep: true
    },

    '$route.query.assetId': {
      immediate: true,
      handler(assetId) {
        if (assetId) {
          this.loadAssetGraph(assetId)
        }
      }
    }
  },

  methods: {
    ...mapActions([
      'loadGlobalGraph',
      'loadAssetGraph',
      'loadProjectGraph',
      'selectNode',
      'saveNodePosition',
      'createManualLink',
      'deleteLink',
      'triggerAutoLink',
      'rebuildGraph',
      'loadGraphStats',
      'setGraphDepth',
      'setGraphFilters'
    ]),

    getNodeTypeLabel(type) {
      return NODE_TYPE_LABELS[type] || type || '未知'
    },

    getNodeTypeColor(type) {
      return NODE_TYPE_COLORS[type] || '#a1a1aa'
    },

    getLinkTypeLabel(type) {
      return LINK_TYPE_LABELS[type] || type || '未知'
    },

    getLinkTypeColor(type) {
      return LINK_TYPE_COLORS[type] || '#a1a1aa'
    },

    getLinkedNodeLabel(link) {
      const nodeId = this.selectedNode.id
      const otherId =
        link.source_node_id === nodeId
          ? link.target_node_id
          : link.source_node_id
      const node = this.assetGraphData.nodes.find((n) => n.id === otherId)
      return node ? node.label || node.name : otherId
    },

    switchView(mode) {
      if (mode === 'global') {
        this.loadGlobalGraph()
      }
      // asset/project views need an ID, show a selector or use route query
    },

    onDepthChange(depth) {
      this.setGraphDepth(depth)
    },

    onFilterChange() {
      this.setGraphFilters({
        nodeTypes: this.localFilterNodeTypes,
        linkTypes: this.localFilterLinkTypes
      })
    },

    refreshGraph() {
      this.loadGlobalGraph()
      this.loadGraphStats()
    },

    clearSelection() {
      this.selectNode(null)
    },

    goToAssetDetail() {
      if (this.selectedNode && this.selectedNode.global_asset_id) {
        this.$router.push({
          name: 'global-asset-library',
          query: { assetId: this.selectedNode.global_asset_id }
        })
      }
    },

    async onAutoLink() {
      if (!this.selectedNode || !this.selectedNode.global_asset_id) return
      try {
        await this.triggerAutoLink(this.selectedNode.global_asset_id)
      } catch (err) {
        console.error('Auto-link failed:', err)
      }
    },

    async onDeleteLink(linkId) {
      try {
        await this.deleteLink(linkId)
      } catch (err) {
        console.error('Delete link failed:', err)
      }
    },

    // ---- D3 Force Graph ----

    initGraph() {
      const svgEl = this.$refs.graphSvg
      if (!svgEl) return

      const svg = d3.select(svgEl)
      svg.selectAll('*').remove()

      // Zoom behavior
      this.zoom = d3.zoom().scaleExtent([0.1, 4]).on('zoom', (event) => {
        this.svgGroup.attr('transform', event.transform)
      })
      svg.call(this.zoom)

      this.svgGroup = svg.append('g')

      // Arrow marker for directed edges
      svg
        .append('defs')
        .append('marker')
        .attr('id', 'arrowhead')
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 25)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', '#666')

      this.renderGraph()
    },

    renderGraph() {
      if (!this.svgGroup) return

      const container = this.$refs.graphViewport
      if (!container) return

      const width = container.clientWidth || 800
      const height = container.clientHeight || 600

      const svg = d3.select(this.$refs.graphSvg)
      svg.attr('width', width).attr('height', height)

      const g = this.svgGroup
      g.selectAll('*').remove()

      const nodes = this.assetGraphData.nodes.map((n) => ({ ...n }))
      const links = this.assetGraphData.links.map((l) => ({
        ...l,
        source: l.source_node_id,
        target: l.target_node_id
      }))

      if (!nodes.length) return

      // Stop previous simulation
      if (this.simulation) this.simulation.stop()

      // Create simulation
      this.simulation = d3
        .forceSimulation(nodes)
        .force(
          'link',
          d3
            .forceLink(links)
            .id((d) => d.id)
            .distance(100)
        )
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(30))

      // Links
      const linkGroup = g
        .append('g')
        .attr('class', 'links')
        .selectAll('line')
        .data(links)
        .join('line')
        .attr('stroke', (d) => this.getLinkTypeColor(d.link_type))
        .attr('stroke-opacity', 0.6)
        .attr('stroke-width', (d) => Math.max(1, (d.weight || 1) * 1.5))
        .attr('marker-end', 'url(#arrowhead)')

      // Nodes
      const nodeGroup = g
        .append('g')
        .attr('class', 'nodes')
        .selectAll('g')
        .data(nodes)
        .join('g')
        .attr('class', 'node-group')
        .call(this.dragBehavior())
        .on('click', (_event, d) => {
          this.selectNode(d)
        })

      nodeGroup
        .append('circle')
        .attr('r', (d) => (d.node_type === 'project' ? 16 : 12))
        .attr('fill', (d) => this.getNodeTypeColor(d.node_type))
        .attr('stroke', '#fff')
        .attr('stroke-width', 2)
        .attr('cursor', 'pointer')

      nodeGroup
        .append('text')
        .text((d) => d.label || d.name || '')
        .attr('dx', 16)
        .attr('dy', 4)
        .attr('font-size', '11px')
        .attr('fill', 'var(--text)')
        .attr('pointer-events', 'none')

      // Tick
      this.simulation.on('tick', () => {
        linkGroup
          .attr('x1', (d) => d.source.x)
          .attr('y1', (d) => d.source.y)
          .attr('x2', (d) => d.target.x)
          .attr('y2', (d) => d.target.y)

        nodeGroup.attr('transform', (d) => `translate(${d.x},${d.y})`)
      })
    },

    dragBehavior() {
      const simulation = this.simulation
      const self = this

      return d3
        .drag()
        .on('start', (event, d) => {
          if (!event.active && simulation) {
            simulation.alphaTarget(0.3).restart()
          }
          d.fx = d.x
          d.fy = d.y
        })
        .on('drag', (event, d) => {
          d.fx = event.x
          d.fy = event.y
        })
        .on('end', (event, d) => {
          if (!event.active && simulation) {
            simulation.alphaTarget(0)
          }
          d.fx = null
          d.fy = null
          self.saveNodePosition({ nodeId: d.id, x: event.x, y: event.y })
        })
    }
  }
}
</script>

<style lang="scss" scoped>
.asset-node-graph {
  display: flex;
  flex-direction: column;
  max-height: 100%;
  height: 100%;
  padding: 4em 2em 1em 2em;
  color: var(--text);
}

.toolbar {
  gap: 1em;
  align-items: center;
  margin-bottom: 1em;
  flex-wrap: wrap;
}

.toolbar-group {
  gap: 0.4em;
  align-items: center;
}

.toolbar-label {
  font-size: 0.85em;
  color: var(--text-alt);
  margin-right: 0.3em;
  white-space: nowrap;
}

.filter-combo {
  min-width: 120px;
}

.graph-container {
  flex: 1;
  min-height: 0;
  gap: 1em;
  align-items: stretch;
}

/* Stats panel */
.stats-panel {
  width: 220px;
  flex-shrink: 0;
  background: var(--background);
  border-radius: 0.8em;
  padding: 1em;
  border: 1px solid var(--border);
  overflow-y: auto;

  h3 {
    font-size: 1em;
    font-weight: 600;
    margin: 0 0 0.8em 0;
    color: var(--text-strong);
  }

  h4 {
    font-size: 0.85em;
    font-weight: 600;
    margin: 1em 0 0.5em 0;
    color: var(--text);
  }
}

.stat-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.4em;
  font-size: 0.9em;
}

.stat-label {
  color: var(--text-alt);
}

.stat-value {
  font-weight: 600;
  color: var(--text-strong);
}

.stat-section {
  margin-top: 1em;
}

.stat-bar-row {
  display: flex;
  align-items: center;
  gap: 0.5em;
  margin-bottom: 0.3em;
  font-size: 0.8em;
}

.stat-bar-label {
  min-width: 4em;
  color: var(--text-alt);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.stat-bar-track {
  flex: 1;
  height: 6px;
  background: var(--background-alt);
  border-radius: 3px;
  overflow: hidden;
}

.stat-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.stat-bar-count {
  min-width: 2em;
  text-align: right;
  color: var(--text);
  font-weight: 600;
}

/* Graph viewport */
.graph-viewport {
  background: var(--background);
  border-radius: 0.8em;
  border: 1px solid var(--border);
  overflow: hidden;
  position: relative;
  min-height: 400px;
}

.graph-svg {
  width: 100%;
  height: 100%;
  display: block;
}

.empty-message {
  padding: 4em;
  color: var(--text-alt);
}

/* Side panel */
.node-detail-panel {
  padding: 1em;
}

.panel-header {
  margin-bottom: 1em;
  align-items: center;

  h2 {
    margin: 0;
    font-size: 1.1em;
  }
}

.panel-section {
  margin-bottom: 1.5em;

  h3 {
    font-size: 0.95em;
    font-weight: 600;
    margin-bottom: 0.5em;
    color: var(--text-strong);
  }
}

.info-row {
  display: flex;
  margin-bottom: 0.5em;
  font-size: 0.9em;
  gap: 0.5em;
}

.info-label {
  color: var(--text-alt);
  min-width: 5em;
  flex-shrink: 0;
}

.info-value {
  color: var(--text);
  display: flex;
  align-items: center;
  gap: 0.3em;
}

.metadata-value {
  font-family: monospace;
  font-size: 0.85em;
  white-space: pre-wrap;
  word-break: break-all;
  background: var(--background-alt);
  padding: 0.3em 0.5em;
  border-radius: 0.3em;
}

.node-type-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

/* Link list */
.link-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.link-item {
  padding: 0.4em 0;
  border-bottom: 1px solid var(--border);
  align-items: center;
  gap: 0.5em;

  &:last-child {
    border-bottom: none;
  }
}

.link-type-badge {
  display: inline-block;
  padding: 0.1em 0.5em;
  border-radius: 0.8em;
  font-size: 0.75em;
  color: #fff;
  white-space: nowrap;
}

.link-target {
  font-size: 0.9em;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.link-delete-btn {
  opacity: 0.5;
  cursor: pointer;

  &:hover {
    opacity: 1;
  }
}

.panel-actions {
  display: flex;
  flex-direction: column;
  gap: 0.5em;
  padding-top: 1em;
  border-top: 1px solid var(--border);
}

/* Toolbar button active state */
:deep(.active) {
  background: var(--background-selected) !important;
  font-weight: 600;
}

/* ComboboxMulti inline styles */
.combobox-multi-wrapper {
  display: inline-flex;
  flex-direction: column;
  gap: 0.3em;
}

.combobox-multi-select {
  background: var(--background);
  color: var(--text);
  border: 1px solid var(--border);
  border-radius: 0.5em;
  padding: 0.3em 0.6em;
  font-size: 0.85em;
  cursor: pointer;
}

.combobox-multi-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.2em;
}

.multi-tag {
  background: var(--background-alt);
  padding: 0.1em 0.5em;
  border-radius: 0.8em;
  font-size: 0.75em;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.2em;

  &:hover {
    background: var(--background-hover);
  }
}

.multi-tag-x {
  font-weight: bold;
  font-size: 1.1em;
  line-height: 1;
}
</style>
