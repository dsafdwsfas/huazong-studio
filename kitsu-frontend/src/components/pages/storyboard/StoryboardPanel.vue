<template>
  <div class="storyboard-panel">
    <div class="storyboard-main">
    <!-- Toolbar -->
    <div class="storyboard-toolbar">
      <div class="layout-toggle">
        <button
          :class="{ active: layout === 'waterfall' }"
          :title="'瀑布流'"
          @click="layout = 'waterfall'"
        >
          <GridIcon :size="18" />
        </button>
        <button
          :class="{ active: layout === 'grid' }"
          :title="'网格'"
          @click="layout = 'grid'"
        >
          <LayoutGridIcon :size="18" />
        </button>
        <button
          :class="{ active: layout === 'timeline' }"
          :title="'时间线'"
          @click="layout = 'timeline'"
        >
          <GanttChartIcon :size="18" />
        </button>
      </div>

      <div class="filters">
        <select v-model="filters.status" class="filter-select" @change="onFilterChange">
          <option value="">全部状态</option>
          <option value="waiting">待机</option>
          <option value="running">进行中</option>
          <option value="complete">完成</option>
          <option value="cancelled">已取消</option>
        </select>
        <select v-model="filters.assignee" class="filter-select" @change="onFilterChange">
          <option value="">全部负责人</option>
          <option
            v-for="person in assigneeList"
            :key="person.id"
            :value="person.id"
          >
            {{ person.name }}
          </option>
        </select>
        <select v-model="filters.sequenceId" class="filter-select" @change="onFilterChange">
          <option value="">全部场景</option>
          <option
            v-for="seq in allSequences"
            :key="seq.id"
            :value="seq.id"
          >
            {{ seq.name }}
          </option>
        </select>
      </div>

      <div class="search">
        <SearchIcon :size="16" class="search-icon" />
        <input
          v-model="searchQuery"
          placeholder="搜索分镜..."
          class="search-input"
          @input="onSearchInput"
        />
      </div>

      <button
        class="btn-camera-lib"
        :title="'镜头语言库'"
        @click="showCameraLibrary = true"
      >
        <CameraIcon :size="16" />
        <span>镜头语言</span>
      </button>
      <button
        class="btn-prompt-lib"
        :title="'提示词库'"
        @click="showPromptLibrary = true"
      >
        <BookOpenIcon :size="16" />
        <span>提示词库</span>
      </button>
      <button
        v-if="isManager"
        class="btn-style-lock"
        :title="'风格锁定'"
        @click="showStyleLock = true"
      >
        <LockIcon :size="16" />
        <span>风格锁定</span>
      </button>
    </div>

    <!-- Batch action bar -->
    <div v-if="selectedShotIds.length > 1" class="batch-bar">
      <span class="batch-info">
        已选 {{ selectedShotIds.length }} 个分镜
      </span>
      <button class="btn-batch" @click="showBatchAssign = true">
        <UsersIcon :size="14" />
        分配
      </button>
      <button class="btn-batch" @click="showBatchStatus = true">
        <TagIcon :size="14" />
        状态
      </button>
      <button class="btn-batch" @click="onBatchDownload">
        <DownloadIcon :size="14" />
        下载
      </button>
      <button class="btn-batch btn-batch-danger" @click="onBatchDelete">
        <Trash2Icon :size="14" />
        删除
      </button>
      <button class="btn-batch" @click="onBatchAnalyze">
        <SparklesIcon :size="14" />
        AI分析
      </button>
      <button class="btn-batch-clear" @click="clearSelection">
        取消
      </button>
    </div>

    <!-- Global upload button (no selection needed) -->
    <div v-if="isManager && selectedShotIds.length <= 1" class="upload-bar">
      <button class="btn-upload-bar" @click="showBatchUpload = true">
        <UploadIcon :size="14" />
        批量上传分镜
      </button>
    </div>

    <!-- Loading state -->
    <div v-if="storyboardIsLoading" class="loading-state">
      <spinner />
    </div>

    <!-- Empty state -->
    <div v-else-if="filteredSequences.length === 0" class="empty-state">
      <p v-if="searchQuery || hasActiveFilters">没有匹配的分镜</p>
      <p v-else>暂无分镜数据</p>
    </div>

    <!-- Timeline view -->
    <TimelineView
      v-else-if="layout === 'timeline'"
      :sequences="filteredSequences"
      :task-statuses="storyboardTaskStatuses"
      :selected-shot-ids="selectedShotIds"
      :project-fps="projectFps"
      @select-shot="onTimelineShotSelect"
      @open-annotation="onTimelineShotOpen"
      @update-timing="onUpdateTiming"
      @batch-update-timing="onBatchUpdateTiming"
      @move-shot="onTimelineMoveShot"
    />

    <!-- Sequence groups (waterfall/grid) -->
    <div v-else class="sequence-groups" ref="scrollContainer">
      <div
        v-for="(sequence, seqIndex) in filteredSequences"
        :key="sequence.id"
        class="sequence-group"
        :draggable="isManager"
        @dragstart="onSeqDragStart($event, seqIndex)"
        @dragover.prevent="onSeqDragOver($event, seqIndex)"
        @drop="onSeqDrop($event, seqIndex)"
        @dragend="seqDragIndex = -1"
        :class="{ 'drag-over': seqDragOverIndex === seqIndex }"
      >
        <div class="sequence-header">
          <div class="seq-left" @click="toggleSequence(sequence.id)">
            <GripVerticalIcon
              v-if="isManager"
              :size="14"
              class="drag-handle"
            />
            <ChevronRightIcon v-if="collapsed[sequence.id]" :size="16" />
            <ChevronDownIcon v-else :size="16" />
            <span class="sequence-name">{{ sequence.name }}</span>
          </div>
          <div class="seq-stats">
            <span class="stat-item" :title="'分镜数'">
              {{ sequence.shot_count || sequence.shots.length }} 个分镜
            </span>
            <span
              v-if="(sequence.shots_done || 0) > 0"
              class="stat-item stat-done"
              :title="'已完成'"
            >
              {{ sequence.shots_done }} 完成
            </span>
            <span
              v-if="(sequence.assignee_count || 0) > 0"
              class="stat-item"
              :title="'负责人数'"
            >
              {{ sequence.assignee_count }} 人
            </span>
          </div>
          <div class="seq-actions" v-if="isManager" @click.stop>
            <button
              class="seq-action-btn"
              title="编辑场景"
              @click="editSequence(sequence)"
            >
              <PencilIcon :size="14" />
            </button>
            <button
              class="seq-action-btn seq-action-danger"
              title="删除场景"
              @click="confirmDeleteSequence(sequence)"
            >
              <Trash2Icon :size="14" />
            </button>
          </div>
        </div>
        <div
          v-show="!collapsed[sequence.id]"
          class="shots-container"
          :class="layout"
        >
          <StoryboardCard
            v-for="shot in sequence.shots"
            :key="shot.id"
            :shot="shot"
            :selected="isSelected(shot.id)"
            :task-statuses="storyboardTaskStatuses"
            @click="onShotClick($event, shot)"
            @dblclick="openShotDetail(shot)"
            @assign="onAssign"
            @status-change="onStatusChange"
            @open-versions="onOpenVersions"
            @open-review="onOpenReview(sequence, $event)"
            @open-analysis="openAnalysisPanel"
          />
        </div>
      </div>

      <!-- Add sequence button -->
      <div v-if="isManager" class="add-sequence-row">
        <button class="btn-add-sequence" @click="addSequence">
          <PlusIcon :size="16" />
          新建场景
        </button>
      </div>
    </div>

    </div><!-- end .storyboard-main -->

    <!-- Version panel sidebar -->
    <VersionPanel
      :active="showVersionPanel"
      :project-id="projectId"
      :shot-id="versionShotId"
      :shot-name="versionShotName"
      @close="showVersionPanel = false"
      @version-changed="onVersionChanged"
    />

    <!-- Batch assign modal -->
    <BatchAssignModal
      :active="showBatchAssign"
      :shot-ids="selectedShotIds"
      @close="showBatchAssign = false"
      @confirm="onBatchAssign"
    />

    <!-- Batch status modal -->
    <BatchStatusModal
      :active="showBatchStatus"
      :shot-ids="selectedShotIds"
      :statuses="storyboardTaskStatuses"
      @close="showBatchStatus = false"
      @confirm="onBatchStatusChange"
    />

    <!-- Batch upload modal -->
    <BatchUploadModal
      :active="showBatchUpload"
      :project-id="projectId"
      @close="showBatchUpload = false"
      @uploaded="onBatchUploaded"
    />

    <!-- Sequence edit modal -->
    <SequenceEditModal
      :active="showSequenceEdit"
      :sequence="editingSequence"
      @close="showSequenceEdit = false"
      @confirm="onSequenceSave"
    />

    <!-- Review panel sidebar -->
    <ReviewPanel
      :active="showReviewPanel"
      :project-id="projectId"
      :shot="reviewShot"
      :shot-name="reviewShot ? reviewShot.name : ''"
      :sequence-name="reviewSequenceName"
      :task-statuses="storyboardTaskStatuses"
      :is-manager="isManager"
      @close="showReviewPanel = false"
      @submit-review="onSubmitReview"
      @status-changed="onReviewStatusChanged"
    />

    <!-- Camera language library -->
    <CameraLanguageLibrary
      v-if="showCameraLibrary"
      :active="showCameraLibrary"
      :project-id="projectId"
      @close="showCameraLibrary = false"
    />

    <!-- Prompt library (fullscreen panel) -->
    <PromptLibrary
      v-if="showPromptLibrary"
      :active="showPromptLibrary"
      :project-id="projectId"
      @close="showPromptLibrary = false"
    />

    <!-- Style lock panel (fullscreen overlay) -->
    <StyleLockPanel
      v-if="showStyleLock"
      :project-id="projectId"
      :project-name="currentProjectName"
      @back="showStyleLock = false"
      @lock-style="onLockStyle"
      @unlock-style="onUnlockStyle"
    />

    <!-- Style analysis panel sidebar -->
    <StyleAnalysisPanel
      :active="showAnalysisPanel"
      :project-id="projectId"
      :shot="analysisShot"
      :analysis-result="analysisResult"
      :is-analyzing="isAnalyzing"
      @close="showAnalysisPanel = false"
      @analyze="onAnalyzeShot"
      @reanalyze="onAnalyzeShot"
    />
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'
import {
  CameraIcon,
  ChevronDownIcon,
  SparklesIcon,
  BookOpenIcon,
  ChevronRightIcon,
  DownloadIcon,
  GanttChartIcon,
  GripVerticalIcon,
  GridIcon,
  LayoutGridIcon,
  LockIcon,
  PencilIcon,
  PlusIcon,
  SearchIcon,
  TagIcon,
  Trash2Icon,
  UploadIcon,
  UsersIcon
} from 'lucide-vue-next'

import StoryboardCard from '@/components/pages/storyboard/StoryboardCard.vue'
import CameraLanguageLibrary from '@/components/pages/storyboard/CameraLanguageLibrary.vue'
import PromptLibrary from '@/components/pages/storyboard/PromptLibrary.vue'
import ReviewPanel from '@/components/pages/storyboard/ReviewPanel.vue'
import StyleAnalysisPanel from '@/components/pages/storyboard/StyleAnalysisPanel.vue'
import StyleLockPanel from '@/components/pages/storyboard/StyleLockPanel.vue'
import TimelineView from '@/components/pages/storyboard/TimelineView.vue'
import BatchAssignModal from '@/components/pages/storyboard/BatchAssignModal.vue'
import BatchStatusModal from '@/components/pages/storyboard/BatchStatusModal.vue'
import BatchUploadModal from '@/components/pages/storyboard/BatchUploadModal.vue'
import SequenceEditModal from '@/components/pages/storyboard/SequenceEditModal.vue'
import VersionPanel from '@/components/pages/storyboard/VersionPanel.vue'

export default {
  name: 'StoryboardPanel',

  components: {
    ChevronDownIcon,
    ChevronRightIcon,
    DownloadIcon,
    GanttChartIcon,
    GripVerticalIcon,
    BookOpenIcon,
    LockIcon,
    GridIcon,
    LayoutGridIcon,
    PencilIcon,
    PlusIcon,
    SearchIcon,
    TagIcon,
    Trash2Icon,
    UploadIcon,
    UsersIcon,
    CameraIcon,
    SparklesIcon,
    StoryboardCard,
    CameraLanguageLibrary,
    PromptLibrary,
    ReviewPanel,
    StyleAnalysisPanel,
    StyleLockPanel,
    TimelineView,
    BatchAssignModal,
    BatchStatusModal,
    BatchUploadModal,
    SequenceEditModal,
    VersionPanel
  },

  data() {
    return {
      layout: 'waterfall',
      searchQuery: '',
      collapsed: {},
      selectedShotIds: [],
      showBatchAssign: false,
      showBatchStatus: false,
      showBatchUpload: false,
      showSequenceEdit: false,
      editingSequence: null,
      showVersionPanel: false,
      versionShotId: '',
      versionShotName: '',
      showReviewPanel: false,
      reviewShot: null,
      reviewSequenceName: '',
      showCameraLibrary: false,
      showPromptLibrary: false,
      showStyleLock: false,
      showAnalysisPanel: false,
      analysisShot: null,
      analysisResult: null,
      isAnalyzing: false,
      seqDragIndex: -1,
      seqDragOverIndex: -1,
      filters: {
        status: '',
        assignee: '',
        sequenceId: ''
      }
    }
  },

  computed: {
    ...mapGetters([
      'storyboardSequences',
      'storyboardTotalShots',
      'storyboardIsLoading',
      'storyboardTaskStatuses',
      'isCurrentUserManager'
    ]),

    isManager() {
      return this.isCurrentUserManager
    },

    projectId() {
      return this.$route.params.production_id
    },

    episodeId() {
      return this.$route.params.episode_id || null
    },

    allSequences() {
      return this.storyboardSequences
    },

    assigneeList() {
      const seen = new Map()
      for (const seq of this.storyboardSequences) {
        for (const shot of seq.shots || []) {
          if (shot.assignees) {
            for (const a of shot.assignees) {
              const id = typeof a === 'string' ? a : a.id
              if (!seen.has(id)) {
                seen.set(id, typeof a === 'object' ? a : { id: a, name: a })
              }
            }
          }
        }
      }
      return Array.from(seen.values()).sort((a, b) =>
        (a.name || '').localeCompare(b.name || '')
      )
    },

    hasActiveFilters() {
      return !!(
        this.filters.status ||
        this.filters.assignee ||
        this.filters.sequenceId
      )
    },

    filteredSequences() {
      let sequences = this.storyboardSequences
      if (!sequences) return []

      if (this.filters.sequenceId) {
        sequences = sequences.filter(
          (seq) => seq.id === this.filters.sequenceId
        )
      }

      return sequences
        .map((seq) => {
          let shots = seq.shots || []

          if (this.filters.status) {
            shots = shots.filter((s) => s.status === this.filters.status)
          }

          if (this.filters.assignee) {
            const filterId = this.filters.assignee
            shots = shots.filter(
              (s) =>
                s.assignees &&
                s.assignees.some((a) => {
                  const id = typeof a === 'string' ? a : a.id
                  return id === filterId
                })
            )
          }

          if (this.searchQuery) {
            const query = this.searchQuery.toLowerCase()
            shots = shots.filter(
              (s) =>
                (s.name && s.name.toLowerCase().includes(query)) ||
                (s.description && s.description.toLowerCase().includes(query))
            )
          }

          return { ...seq, shots }
        })
        .filter((seq) => seq.shots.length > 0)
    },

    currentProjectName() {
      return this.$store.getters.currentProduction?.name || ''
    },

    projectFps() {
      // Derive from first shot that has fps, default 24
      for (const seq of this.storyboardSequences) {
        for (const shot of seq.shots || []) {
          if (shot.fps) return shot.fps
        }
      }
      return 24
    },

    flatShots() {
      const shots = []
      for (const seq of this.filteredSequences) {
        if (!this.collapsed[seq.id]) {
          shots.push(...seq.shots)
        }
      }
      return shots
    }
  },

  mounted() {
    this.loadData()
    window.addEventListener('keydown', this.onKeydown)
  },

  beforeUnmount() {
    window.removeEventListener('keydown', this.onKeydown)
  },

  methods: {
    ...mapActions([
      'loadStoryboard',
      'loadTaskStatuses',
      'assignShot',
      'updateShotStatus',
      'batchAssignShots',
      'batchUpdateStatus',
      'batchDeleteShots',
      'reorderShots',
      'reorderSequences',
      'createSequence',
      'updateSequence',
      'deleteSequence',
      'setStoryboardFilter',
      'updateShotTiming',
      'batchUpdateTiming',
      'submitReview',
      'analyzeShot',
      'loadShotAnalysis'
    ]),

    async loadData() {
      if (this.projectId) {
        await Promise.all([
          this.loadStoryboard({
            projectId: this.projectId,
            episodeId: this.episodeId
          }),
          this.loadTaskStatuses({ projectId: this.projectId })
        ])
      }
    },

    isSelected(shotId) {
      return this.selectedShotIds.includes(shotId)
    },

    toggleSequence(sequenceId) {
      this.collapsed = {
        ...this.collapsed,
        [sequenceId]: !this.collapsed[sequenceId]
      }
    },

    onShotClick(event, shot) {
      // Ctrl/Cmd+click for multi-select
      if (event.ctrlKey || event.metaKey) {
        const idx = this.selectedShotIds.indexOf(shot.id)
        if (idx >= 0) {
          this.selectedShotIds.splice(idx, 1)
        } else {
          this.selectedShotIds.push(shot.id)
        }
      } else {
        this.selectedShotIds = [shot.id]
      }
      this.$emit('shot-selected', shot)
    },

    clearSelection() {
      this.selectedShotIds = []
    },

    openShotDetail(shot) {
      this.$emit('shot-detail', shot)
    },

    async onAssign({ shotId, personIds, taskId }) {
      try {
        await this.assignShot({
          projectId: this.projectId,
          shotId,
          personIds,
          taskId
        })
      } catch (err) {
        console.error('Failed to assign shot:', err)
      }
    },

    async onStatusChange({ shotId, taskStatusId, taskId }) {
      try {
        await this.updateShotStatus({
          projectId: this.projectId,
          shotId,
          taskStatusId,
          taskId
        })
      } catch (err) {
        console.error('Failed to update status:', err)
      }
    },

    async onBatchAssign({ shotIds, personIds }) {
      try {
        await this.batchAssignShots({
          projectId: this.projectId,
          shotIds,
          personIds
        })
        // Reload to get updated assignee data
        await this.loadStoryboard({
          projectId: this.projectId,
          episodeId: this.episodeId
        })
        this.showBatchAssign = false
        this.selectedShotIds = []
      } catch (err) {
        console.error('Failed to batch assign:', err)
      }
    },

    async onBatchStatusChange({ shotIds, taskStatusId }) {
      try {
        await this.batchUpdateStatus({
          projectId: this.projectId,
          shotIds,
          taskStatusId
        })
        await this.loadStoryboard({
          projectId: this.projectId,
          episodeId: this.episodeId
        })
        this.showBatchStatus = false
        this.selectedShotIds = []
      } catch (err) {
        console.error('Failed to batch update status:', err)
      }
    },

    async onBatchDownload() {
      try {
        const response = await fetch(
          `/api/data/projects/${this.projectId}/storyboard/batch-download`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({ shot_ids: this.selectedShotIds })
          }
        )
        if (!response.ok) throw new Error('Download failed')
        const blob = await response.blob()
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'storyboard-export.zip'
        a.click()
        URL.revokeObjectURL(url)
      } catch (err) {
        console.error('Failed to batch download:', err)
      }
    },

    async onBatchDelete() {
      const count = this.selectedShotIds.length
      if (!confirm(`确定要取消 ${count} 个分镜吗？`)) return
      try {
        await this.batchDeleteShots({
          projectId: this.projectId,
          shotIds: this.selectedShotIds,
          hardDelete: false
        })
        await this.loadStoryboard({
          projectId: this.projectId,
          episodeId: this.episodeId
        })
        this.selectedShotIds = []
      } catch (err) {
        console.error('Failed to batch delete:', err)
      }
    },

    async onBatchUploaded() {
      await this.loadStoryboard({
        projectId: this.projectId,
        episodeId: this.episodeId
      })
      this.showBatchUpload = false
    },

    // Version management
    onOpenVersions(shot) {
      this.versionShotId = shot.id
      this.versionShotName = shot.name
      this.showVersionPanel = true
    },

    async onVersionChanged() {
      // Reload storyboard to get updated preview_file_id
      await this.loadStoryboard({
        projectId: this.projectId,
        episodeId: this.episodeId
      })
    },

    // Scene management
    addSequence() {
      this.editingSequence = null
      this.showSequenceEdit = true
    },

    editSequence(sequence) {
      this.editingSequence = sequence
      this.showSequenceEdit = true
    },

    async onSequenceSave({ id, name, description }) {
      try {
        if (id) {
          await this.updateSequence({
            projectId: this.projectId,
            sequenceId: id,
            name,
            description
          })
        } else {
          await this.createSequence({
            projectId: this.projectId,
            episodeId: this.episodeId,
            name,
            description
          })
        }
        this.showSequenceEdit = false
      } catch (err) {
        console.error('Failed to save sequence:', err)
      }
    },

    async confirmDeleteSequence(sequence) {
      const shotCount = sequence.shot_count || sequence.shots?.length || 0
      if (shotCount > 0) {
        alert(`无法删除：该场景下还有 ${shotCount} 个分镜。请先移动或删除所有分镜。`)
        return
      }
      if (!confirm(`确定要删除场景 "${sequence.name}" 吗？`)) return
      try {
        await this.deleteSequence({
          projectId: this.projectId,
          episodeId: this.episodeId,
          sequenceId: sequence.id
        })
      } catch (err) {
        console.error('Failed to delete sequence:', err)
      }
    },

    // Sequence drag-and-drop
    onSeqDragStart(event, index) {
      this.seqDragIndex = index
      event.dataTransfer.effectAllowed = 'move'
      event.dataTransfer.setData('text/plain', String(index))
    },

    onSeqDragOver(event, index) {
      if (this.seqDragIndex === -1) return
      this.seqDragOverIndex = index
    },

    async onSeqDrop(event, toIndex) {
      this.seqDragOverIndex = -1
      const fromIndex = this.seqDragIndex
      this.seqDragIndex = -1
      if (fromIndex === toIndex || fromIndex === -1) return

      const sequences = [...this.filteredSequences]
      const [moved] = sequences.splice(fromIndex, 1)
      sequences.splice(toIndex, 0, moved)

      // Build order payload
      const sequenceOrders = sequences.map((seq, i) => ({
        sequence_id: seq.id,
        order: i
      }))

      // Optimistic update
      this.$store.commit('REORDER_SEQUENCES', sequenceOrders)

      try {
        await this.reorderSequences({
          projectId: this.projectId,
          sequenceOrders
        })
      } catch (err) {
        console.error('Failed to reorder sequences:', err)
        // Reload on failure
        await this.loadStoryboard({
          projectId: this.projectId,
          episodeId: this.episodeId
        })
      }
    },

    onFilterChange() {
      for (const [key, value] of Object.entries(this.filters)) {
        this.setStoryboardFilter({ key, value })
      }
    },

    onSearchInput() {
      // Debounced search is handled reactively via computed
    },

    // Timeline event handlers
    onTimelineShotSelect({ shotId, ctrlKey }) {
      if (ctrlKey) {
        const idx = this.selectedShotIds.indexOf(shotId)
        if (idx >= 0) {
          this.selectedShotIds.splice(idx, 1)
        } else {
          this.selectedShotIds.push(shotId)
        }
      } else {
        this.selectedShotIds = [shotId]
      }
    },

    onTimelineShotOpen({ shotId }) {
      const shot = this.findShotById(shotId)
      if (shot) this.openShotDetail(shot)
    },

    async onUpdateTiming({ shotId, frameIn, frameOut, nbFrames }) {
      try {
        await this.updateShotTiming({
          projectId: this.projectId,
          shotId,
          timing: {
            frame_in: frameIn,
            frame_out: frameOut,
            nb_frames: nbFrames
          }
        })
      } catch (err) {
        console.error('Failed to update shot timing:', err)
      }
    },

    async onBatchUpdateTiming(shots) {
      try {
        await this.batchUpdateTiming({
          projectId: this.projectId,
          shots: shots.map((s) => ({
            shot_id: s.shotId,
            frame_in: s.frameIn,
            frame_out: s.frameOut,
            nb_frames: s.nbFrames
          }))
        })
      } catch (err) {
        console.error('Failed to batch update timing:', err)
      }
    },

    async onTimelineMoveShot({ shotId, targetSequenceId, position }) {
      // Reorder shot to new sequence — reuse existing reorder mechanism
      const allOrders = []
      for (const seq of this.storyboardSequences) {
        for (const shot of seq.shots) {
          allOrders.push({
            shot_id: shot.id,
            order: shot.storyboard_order || 0,
            sequence_id: shot.id === shotId ? targetSequenceId : seq.id
          })
        }
      }
      try {
        await this.reorderShots({
          projectId: this.projectId,
          shotOrders: allOrders
        })
        await this.loadStoryboard({
          projectId: this.projectId,
          episodeId: this.episodeId
        })
      } catch (err) {
        console.error('Failed to move shot:', err)
      }
    },

    onOpenReview(sequence, shot) {
      this.openReviewPanel(shot, sequence.name)
    },

    // Review panel methods
    openReviewPanel(shot, sequenceName) {
      this.reviewShot = shot
      this.reviewSequenceName = sequenceName || ''
      this.showReviewPanel = true
    },

    async onSubmitReview({ shotId, taskId, comment, action, taskStatusId }) {
      try {
        await this.submitReview({
          projectId: this.projectId,
          shotId,
          action,
          text: comment,
          taskId
        })
        // Reload to reflect status changes
        await this.loadStoryboard({
          projectId: this.projectId,
          episodeId: this.episodeId
        })
      } catch (err) {
        console.error('Failed to submit review:', err)
      }
    },

    async onReviewStatusChanged() {
      await this.loadStoryboard({
        projectId: this.projectId,
        episodeId: this.episodeId
      })
    },

    // Batch AI analysis (3.8)
    async onBatchAnalyze() {
      if (!this.selectedShotIds.length) return
      try {
        await this.$store.dispatch('batchAnalyzeShots', {
          projectId: this.projectId,
          shotIds: this.selectedShotIds
        })
        await this.loadStoryboard({
          projectId: this.projectId,
          episodeId: this.episodeId
        })
        this.selectedShotIds = []
      } catch (err) {
        console.error('Batch analyze failed:', err)
      }
    },

    // Style lock methods
    async onLockStyle({ style, referenceImageIds }) {
      try {
        await this.$store.dispatch('lockStyle', {
          projectId: this.projectId,
          style,
          referenceImageIds
        })
      } catch (err) {
        console.error('Failed to lock style:', err)
      }
    },

    async onUnlockStyle() {
      try {
        await this.$store.dispatch('unlockStyle', {
          projectId: this.projectId
        })
      } catch (err) {
        console.error('Failed to unlock style:', err)
      }
    },

    // Style analysis methods
    async openAnalysisPanel(shot) {
      this.analysisShot = shot
      this.analysisResult = null
      this.showAnalysisPanel = true
      // Load existing analysis
      try {
        const data = await this.loadShotAnalysis({
          projectId: this.projectId,
          shotId: shot.id
        })
        if (data && data.status === 'success') {
          this.analysisResult = data
        }
      } catch {
        // No existing analysis
      }
    },

    async onAnalyzeShot({ shotId }) {
      this.isAnalyzing = true
      try {
        const result = await this.analyzeShot({
          projectId: this.projectId,
          shotId
        })
        this.analysisResult = result
      } catch (err) {
        console.error('Failed to analyze shot:', err)
      } finally {
        this.isAnalyzing = false
      }
    },

    findShotById(shotId) {
      for (const seq of this.storyboardSequences) {
        const shot = (seq.shots || []).find((s) => s.id === shotId)
        if (shot) return shot
      }
      return null
    },

    onKeydown(event) {
      if (
        event.target.tagName === 'INPUT' ||
        event.target.tagName === 'TEXTAREA' ||
        event.target.tagName === 'SELECT'
      ) {
        return
      }

      const shots = this.flatShots
      if (!shots.length) return

      const currentId =
        this.selectedShotIds.length > 0
          ? this.selectedShotIds[this.selectedShotIds.length - 1]
          : null
      const currentIndex = shots.findIndex((s) => s.id === currentId)

      if (event.key === 'ArrowRight' || event.key === 'ArrowDown') {
        event.preventDefault()
        const nextIndex =
          currentIndex < shots.length - 1 ? currentIndex + 1 : 0
        this.selectedShotIds = [shots[nextIndex].id]
        this.$emit('shot-selected', shots[nextIndex])
      } else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') {
        event.preventDefault()
        const prevIndex =
          currentIndex > 0 ? currentIndex - 1 : shots.length - 1
        this.selectedShotIds = [shots[prevIndex].id]
        this.$emit('shot-selected', shots[prevIndex])
      } else if (event.key === 'Enter' && currentId) {
        event.preventDefault()
        const shot = shots.find((s) => s.id === currentId)
        if (shot) this.openShotDetail(shot)
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.storyboard-panel {
  display: flex;
  height: 100%;
  overflow: hidden;
}

.storyboard-main {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.storyboard-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.btn-camera-lib {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: transparent;
  color: var(--text);
  font-size: 0.8rem;
  cursor: pointer;

  &:hover {
    background: var(--background-alt, rgba(255, 255, 255, 0.05));
    border-color: #0abde3;
    color: #0abde3;
  }
}

.btn-prompt-lib {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: transparent;
  color: var(--text);
  font-size: 0.8rem;
  cursor: pointer;

  &:hover {
    background: var(--background-alt, rgba(255, 255, 255, 0.05));
    border-color: #ff9f43;
    color: #ff9f43;
  }
}

.btn-style-lock {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: transparent;
  color: var(--text);
  font-size: 0.8rem;
  cursor: pointer;
  margin-left: auto;

  &:hover {
    background: var(--background-alt, rgba(255, 255, 255, 0.05));
    border-color: var(--color-primary);
    color: var(--color-primary);
  }
}

.layout-toggle {
  display: flex;
  gap: 2px;

  button {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: none;
    border-radius: 4px;
    background: transparent;
    color: var(--text);
    cursor: pointer;
    transition: background 0.15s;

    &:hover {
      background: var(--background-alt);
    }

    &.active {
      background: var(--background-selectable);
    }
  }
}

.filters {
  display: flex;
  gap: 8px;
  flex: 1;
}

.filter-select {
  padding: 4px 8px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--background);
  color: var(--text);
  font-size: 0.85rem;
  cursor: pointer;

  &:focus {
    outline: none;
    border-color: var(--color-primary);
  }
}

.search {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 8px;
  color: var(--text-alt);
  pointer-events: none;
}

.search-input {
  padding: 4px 8px 4px 28px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--background);
  color: var(--text);
  font-size: 0.85rem;
  width: 180px;
  transition: border-color 0.15s;

  &::placeholder {
    color: var(--text-alt);
  }

  &:focus {
    outline: none;
    border-color: var(--color-primary);
  }
}

.batch-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  background: var(--color-primary);
  color: #fff;
  font-size: 0.85rem;
  flex-shrink: 0;
}

.batch-info {
  flex: 1;
  font-weight: 500;
}

.btn-batch {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  border: 1px solid rgba(255, 255, 255, 0.4);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
  font-size: 0.8rem;
  cursor: pointer;

  &:hover {
    background: rgba(255, 255, 255, 0.25);
  }
}

.btn-batch-danger {
  border-color: rgba(255, 100, 100, 0.4);

  &:hover {
    background: rgba(255, 100, 100, 0.25);
  }
}

.upload-bar {
  padding: 4px 16px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.btn-upload-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border: 1px dashed var(--border);
  border-radius: 4px;
  background: transparent;
  color: var(--text-alt);
  font-size: 0.8rem;
  cursor: pointer;

  &:hover {
    border-color: var(--color-primary);
    color: var(--color-primary);
  }
}

.btn-batch-clear {
  padding: 4px 12px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.8rem;
  cursor: pointer;

  &:hover {
    color: #fff;
  }
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4rem;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4rem;
  color: var(--text-alt);
  font-size: 0.95rem;
}

.sequence-groups {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}

.sequence-group {
  &:not(:last-child) {
    border-bottom: 1px solid var(--border);
  }

  &.drag-over {
    border-top: 2px solid var(--color-primary);
  }
}

.sequence-header {
  display: flex;
  align-items: center;
  padding: 0.5rem 1rem;
  font-weight: 600;
  gap: 0.5rem;
  background: var(--background-alt);
  user-select: none;
  transition: background 0.15s;

  &:hover {
    background: var(--background-hover);

    .seq-actions {
      opacity: 1;
    }
  }
}

.seq-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  flex: 1;
  min-width: 0;
}

.drag-handle {
  color: var(--text-alt);
  opacity: 0.4;
  cursor: grab;

  &:hover {
    opacity: 1;
  }
}

.sequence-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.seq-stats {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.stat-item {
  font-size: 0.75rem;
  font-weight: 400;
  color: var(--text-alt);
  white-space: nowrap;
}

.stat-done {
  color: #00b242;
}

.seq-actions {
  display: flex;
  gap: 2px;
  opacity: 0;
  transition: opacity 0.15s;
  flex-shrink: 0;
}

.seq-action-btn {
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--text-alt);
  cursor: pointer;

  &:hover {
    background: var(--background-hover);
    color: var(--text);
  }

  &.seq-action-danger:hover {
    color: #e53935;
    background: #fce4ec;
  }
}

.add-sequence-row {
  padding: 0.5rem 1rem;
}

.btn-add-sequence {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1px dashed var(--border);
  border-radius: 6px;
  background: transparent;
  color: var(--text-alt);
  font-size: 0.85rem;
  cursor: pointer;
  width: 100%;
  justify-content: center;
  transition: all 0.15s;

  &:hover {
    border-color: var(--color-primary);
    color: var(--color-primary);
    background: rgba(var(--color-primary-rgb, 0, 120, 255), 0.05);
  }
}

.shots-container {
  padding: 1rem;

  &.waterfall {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;

    .storyboard-card {
      width: 180px;
    }
  }

  &.grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 12px;
  }
}
</style>
