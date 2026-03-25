<template>
  <div
    class="storyboard-card"
    :class="{
      selected,
      'status-complete': isDone
    }"
    @click="$emit('click', shot)"
    @dblclick="$emit('dblclick', shot)"
  >
    <div class="card-thumbnail">
      <img
        v-if="shot.preview_file_id"
        :src="thumbnailUrl"
        :alt="shot.name"
        loading="lazy"
      />
      <div v-else class="empty-thumbnail">
        <ImageIcon :size="24" />
      </div>
      <span v-if="isVideo" class="video-badge" title="视频分镜">
        <VideoIcon :size="12" />
      </span>
      <span v-else-if="isAudio" class="audio-badge" title="音频分镜">
        <Music2Icon :size="12" />
      </span>
      <button
        class="analysis-badge"
        title="AI 风格分析"
        @click.stop="$emit('open-analysis', shot)"
      >
        <SparklesIcon :size="12" />
      </button>
      <button
        class="review-badge"
        title="评审"
        @click.stop="$emit('open-review', shot)"
      >
        <MessageSquareIcon :size="12" />
      </button>
      <button
        v-if="shot.preview_file_id"
        class="version-badge"
        title="版本管理"
        @click.stop="$emit('open-versions', shot)"
      >
        <LayersIcon :size="12" />
      </button>
    </div>
    <div class="card-info">
      <div class="card-header">
        <span class="shot-name">{{ shot.name }}</span>
        <task-status-badge
          v-if="shot.primary_task"
          :task-status-id="shot.primary_task.task_status_id"
          :task-status-name="shot.primary_task.task_status_name"
          :task-status-color="shot.primary_task.task_status_color"
          :statuses="taskStatuses"
          :disabled="!canEditStatus"
          @update="onStatusChange"
        />
        <span v-else class="status-badge badge-waiting">待机</span>
      </div>
      <div class="card-meta">
        <assignee-selector
          :assignees="shot.assignees || []"
          :disabled="!canAssign"
          @update="onAssigneeChange"
        />
        <span v-if="shot.nb_frames" class="frames">{{ shot.nb_frames }}帧</span>
      </div>
      <div class="card-progress" v-if="shot.task_count > 0">
        <div class="progress-bar">
          <div
            class="progress-fill"
            :style="{ width: progressPercent + '%' }"
          ></div>
        </div>
        <span class="progress-text">
          {{ shot.tasks_done }}/{{ shot.task_count }}
        </span>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { ImageIcon, LayersIcon, MessageSquareIcon, Music2Icon, SparklesIcon, VideoIcon } from 'lucide-vue-next'
import TaskStatusBadge from './TaskStatusBadge.vue'
import AssigneeSelector from './AssigneeSelector.vue'

export default {
  name: 'StoryboardCard',

  components: {
    ImageIcon,
    LayersIcon,
    MessageSquareIcon,
    Music2Icon,
    SparklesIcon,
    VideoIcon,
    TaskStatusBadge,
    AssigneeSelector
  },

  props: {
    shot: {
      type: Object,
      required: true
    },
    selected: {
      type: Boolean,
      default: false
    },
    taskStatuses: {
      type: Array,
      default: () => []
    }
  },

  emits: ['click', 'dblclick', 'assign', 'status-change', 'open-versions', 'open-review', 'open-analysis'],

  computed: {
    ...mapGetters(['isCurrentUserManager']),

    thumbnailUrl() {
      return `/api/pictures/thumbnails-square/preview-files/${this.shot.preview_file_id}.png`
    },

    isDone() {
      return this.shot.primary_task?.is_done || false
    },

    progressPercent() {
      if (!this.shot.task_count) return 0
      return Math.round((this.shot.tasks_done / this.shot.task_count) * 100)
    },

    canAssign() {
      return this.isCurrentUserManager
    },

    canEditStatus() {
      return true // Permission checked server-side
    },

    isVideo() {
      const ext = this.shot.preview_file_extension || ''
      return ['mp4', 'mov', 'avi', 'mkv', 'webm', 'wmv', 'm4v'].includes(ext.toLowerCase())
    },

    isAudio() {
      const ext = this.shot.preview_file_extension || ''
      return ['mp3', 'wav'].includes(ext.toLowerCase())
    }
  },

  methods: {
    onAssigneeChange(personIds) {
      this.$emit('assign', {
        shotId: this.shot.id,
        personIds,
        taskId: this.shot.primary_task?.id
      })
    },

    onStatusChange(taskStatusId) {
      this.$emit('status-change', {
        shotId: this.shot.id,
        taskStatusId,
        taskId: this.shot.primary_task?.id
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.storyboard-card {
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--border);
  background: var(--background);
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    transform: translateY(-2px);
  }

  &.selected {
    border-color: var(--color-primary);
  }

  &.status-complete {
    opacity: 0.7;
  }
}

.card-thumbnail {
  position: relative;

  img {
    width: 100%;
    aspect-ratio: 16 / 9;
    object-fit: cover;
    display: block;
  }
}

.version-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.5);
  color: #fff;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s;

  .card-thumbnail:hover & {
    opacity: 1;
  }

  &:hover {
    background: rgba(0, 0, 0, 0.7);
  }
}

.video-badge {
  position: absolute;
  top: 4px;
  left: 4px;
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.6);
  color: #0abde3;
}

.analysis-badge {
  position: absolute;
  bottom: 4px;
  left: 4px;
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.5);
  color: #ffd32a;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s;

  .card-thumbnail:hover & {
    opacity: 1;
  }

  &:hover {
    background: rgba(0, 0, 0, 0.7);
  }
}

.review-badge {
  position: absolute;
  bottom: 4px;
  right: 4px;
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.5);
  color: #fff;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s;

  .card-thumbnail:hover & {
    opacity: 1;
  }

  &:hover {
    background: rgba(0, 0, 0, 0.7);
  }
}

.audio-badge {
  position: absolute;
  top: 4px;
  left: 4px;
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.6);
  color: #10ac84;
}

.empty-thumbnail {
  aspect-ratio: 16 / 9;
  background: var(--background-alt);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-alt);
}

.card-info {
  padding: 8px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 4px;
  margin-bottom: 4px;
}

.shot-name {
  font-weight: 600;
  font-size: 0.85rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-badge {
  font-size: 0.65rem;
  padding: 1px 6px;
  border-radius: 4px;
  white-space: nowrap;
  flex-shrink: 0;
}

.badge-waiting {
  background: #e8eaf6;
  color: #5c6bc0;
}

.card-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  font-size: 0.75rem;
  color: var(--text-alt);
  margin-bottom: 4px;
}

.card-progress {
  display: flex;
  align-items: center;
  gap: 6px;
}

.progress-bar {
  flex: 1;
  height: 4px;
  background: var(--background-alt);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--color-primary);
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 0.65rem;
  color: var(--text-alt);
  white-space: nowrap;
}
</style>
