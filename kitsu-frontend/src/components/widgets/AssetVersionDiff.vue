<template>
  <div class="asset-version-diff">
    <div class="diff-header flexrow">
      <div class="diff-column version-a">
        <div class="version-label">
          <span class="version-number">v{{ versionA.number }}</span>
          <span class="version-meta">
            {{ formatDate(versionA.created_at) }}
            <template v-if="versionA.author">
              &middot; {{ versionA.author }}
            </template>
          </span>
        </div>
      </div>
      <div class="diff-column version-b">
        <div class="version-label">
          <span class="version-number">v{{ versionB.number }}</span>
          <span class="version-meta">
            {{ formatDate(versionB.created_at) }}
            <template v-if="versionB.author">
              &middot; {{ versionB.author }}
            </template>
          </span>
        </div>
      </div>
    </div>

    <div
      class="diff-empty"
      v-if="!diff || !Object.keys(diff).length"
    >
      两个版本之间无差异
    </div>

    <div
      class="diff-row"
      :class="{ collapsed: collapsedFields[field] }"
      :key="field"
      v-for="field in sortedFields"
    >
      <div
        class="diff-field-header"
        @click="toggleCollapse(field)"
      >
        <span class="field-name">{{ getFieldLabel(field) }}</span>
        <span
          class="change-badge"
          :class="getChangeType(field)"
        >
          {{ getChangeBadge(field) }}
        </span>
        <span class="collapse-icon">
          {{ collapsedFields[field] ? '&#9654;' : '&#9660;' }}
        </span>
      </div>

      <div class="diff-field-body flexrow" v-show="!collapsedFields[field]">
        <!-- Array fields (tags, style_keywords) -->
        <template v-if="isArrayField(field)">
          <div class="diff-column version-a">
            <div class="array-diff">
              <span
                class="tag-chip"
                :class="{ removed: isRemovedItem(field, item) }"
                :key="'a-' + item"
                v-for="item in getOldArray(field)"
              >
                {{ item }}
                <span class="diff-indicator" v-if="isRemovedItem(field, item)">-</span>
              </span>
            </div>
          </div>
          <div class="diff-column version-b">
            <div class="array-diff">
              <span
                class="tag-chip"
                :class="{ added: isAddedItem(field, item) }"
                :key="'b-' + item"
                v-for="item in getNewArray(field)"
              >
                {{ item }}
                <span class="diff-indicator" v-if="isAddedItem(field, item)">+</span>
              </span>
            </div>
          </div>
        </template>

        <!-- JSON / object fields (metadata) -->
        <template v-else-if="isObjectField(field)">
          <div class="diff-column version-a">
            <div class="json-diff">
              <div
                class="json-row"
                :class="{ removed: isRemovedKey(field, key) }"
                :key="'a-' + key"
                v-for="(value, key) in getOldObject(field)"
              >
                <span class="json-key">{{ key }}:</span>
                <span class="json-value">{{ formatJsonValue(value) }}</span>
              </div>
            </div>
          </div>
          <div class="diff-column version-b">
            <div class="json-diff">
              <div
                class="json-row"
                :class="{
                  added: isAddedKey(field, key),
                  changed: isChangedKey(field, key)
                }"
                :key="'b-' + key"
                v-for="(value, key) in getNewObject(field)"
              >
                <span class="json-key">{{ key }}:</span>
                <span class="json-value">{{ formatJsonValue(value) }}</span>
              </div>
            </div>
          </div>
        </template>

        <!-- File list fields -->
        <template v-else-if="isFileField(field)">
          <div class="diff-column version-a">
            <div class="file-diff">
              <div
                class="file-item"
                :class="{ removed: isRemovedFile(field, file) }"
                :key="'a-' + (file.id || index)"
                v-for="(file, index) in getOldFiles(field)"
              >
                <div class="file-thumb" v-if="file.thumbnail_url">
                  <img :src="file.thumbnail_url" :alt="file.name || file.filename" />
                </div>
                <span class="file-name">{{ file.name || file.filename }}</span>
              </div>
            </div>
          </div>
          <div class="diff-column version-b">
            <div class="file-diff">
              <div
                class="file-item"
                :class="{ added: isAddedFile(field, file) }"
                :key="'b-' + (file.id || index)"
                v-for="(file, index) in getNewFiles(field)"
              >
                <div class="file-thumb" v-if="file.thumbnail_url">
                  <img :src="file.thumbnail_url" :alt="file.name || file.filename" />
                </div>
                <span class="file-name">{{ file.name || file.filename }}</span>
              </div>
            </div>
          </div>
        </template>

        <!-- Text / scalar fields -->
        <template v-else>
          <div class="diff-column version-a">
            <div class="text-diff old-value">
              {{ formatValue(diff[field].old) }}
            </div>
          </div>
          <div class="diff-column version-b">
            <div class="text-diff new-value">
              {{ formatValue(diff[field].new) }}
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script>
const FIELD_LABELS = {
  name: '名称',
  description: '描述',
  category: '分类',
  category_id: '分类',
  status: '状态',
  tags: '标签',
  style_keywords: '风格关键词',
  metadata: '元数据',
  files: '文件',
  preview_url: '预览图',
  thumbnail_url: '缩略图',
  usage_count: '使用次数',
  linked_projects: '关联项目'
}

const ARRAY_FIELDS = ['tags', 'style_keywords', 'linked_projects']
const OBJECT_FIELDS = ['metadata']
const FILE_FIELDS = ['files']

export default {
  name: 'asset-version-diff',

  props: {
    diff: {
      type: Object,
      default: () => ({})
    },
    versionA: {
      type: Object,
      default: () => ({ number: 0, created_at: '', author: '' })
    },
    versionB: {
      type: Object,
      default: () => ({ number: 0, created_at: '', author: '' })
    }
  },

  data() {
    return {
      collapsedFields: {}
    }
  },

  computed: {
    sortedFields() {
      if (!this.diff) return []
      return Object.keys(this.diff).sort((a, b) => {
        const order = ['name', 'description', 'category', 'status', 'tags', 'style_keywords', 'files', 'metadata']
        const ia = order.indexOf(a)
        const ib = order.indexOf(b)
        if (ia === -1 && ib === -1) return a.localeCompare(b)
        if (ia === -1) return 1
        if (ib === -1) return -1
        return ia - ib
      })
    }
  },

  methods: {
    formatDate(dateStr) {
      if (!dateStr) return ''
      const d = new Date(dateStr)
      const year = d.getFullYear()
      const month = String(d.getMonth() + 1).padStart(2, '0')
      const day = String(d.getDate()).padStart(2, '0')
      const hours = String(d.getHours()).padStart(2, '0')
      const minutes = String(d.getMinutes()).padStart(2, '0')
      return `${year}-${month}-${day} ${hours}:${minutes}`
    },

    getFieldLabel(field) {
      return FIELD_LABELS[field] || field
    },

    isArrayField(field) {
      return ARRAY_FIELDS.includes(field) ||
        (this.diff[field] && Array.isArray(this.diff[field].old)) ||
        (this.diff[field] && Array.isArray(this.diff[field].new))
    },

    isObjectField(field) {
      if (OBJECT_FIELDS.includes(field)) return true
      const d = this.diff[field]
      if (!d) return false
      return (
        (d.old && typeof d.old === 'object' && !Array.isArray(d.old)) ||
        (d.new && typeof d.new === 'object' && !Array.isArray(d.new))
      )
    },

    isFileField(field) {
      return FILE_FIELDS.includes(field)
    },

    getChangeType(field) {
      const d = this.diff[field]
      if (!d) return ''
      if (!d.old && d.new) return 'added'
      if (d.old && !d.new) return 'removed'
      return 'changed'
    },

    getChangeBadge(field) {
      const type = this.getChangeType(field)
      if (type === 'added') return '+ 新增'
      if (type === 'removed') return '- 移除'
      return '~ 变更'
    },

    toggleCollapse(field) {
      this.collapsedFields = {
        ...this.collapsedFields,
        [field]: !this.collapsedFields[field]
      }
    },

    formatValue(value) {
      if (value === null || value === undefined) return '(空)'
      if (typeof value === 'boolean') return value ? '是' : '否'
      return String(value)
    },

    formatJsonValue(value) {
      if (value === null || value === undefined) return 'null'
      if (typeof value === 'object') return JSON.stringify(value)
      return String(value)
    },

    // Array helpers
    getOldArray(field) {
      return (this.diff[field] && this.diff[field].old) || []
    },

    getNewArray(field) {
      return (this.diff[field] && this.diff[field].new) || []
    },

    isRemovedItem(field, item) {
      const newArr = this.getNewArray(field)
      return !newArr.includes(item)
    },

    isAddedItem(field, item) {
      const oldArr = this.getOldArray(field)
      return !oldArr.includes(item)
    },

    // Object helpers
    getOldObject(field) {
      return (this.diff[field] && this.diff[field].old) || {}
    },

    getNewObject(field) {
      return (this.diff[field] && this.diff[field].new) || {}
    },

    isRemovedKey(field, key) {
      const newObj = this.getNewObject(field)
      return !(key in newObj)
    },

    isAddedKey(field, key) {
      const oldObj = this.getOldObject(field)
      return !(key in oldObj)
    },

    isChangedKey(field, key) {
      const oldObj = this.getOldObject(field)
      const newObj = this.getNewObject(field)
      if (!(key in oldObj)) return false
      return JSON.stringify(oldObj[key]) !== JSON.stringify(newObj[key])
    },

    // File helpers
    getOldFiles(field) {
      return (this.diff[field] && this.diff[field].old) || []
    },

    getNewFiles(field) {
      return (this.diff[field] && this.diff[field].new) || []
    },

    isRemovedFile(field, file) {
      const newFiles = this.getNewFiles(field)
      return !newFiles.some((f) => f.id === file.id)
    },

    isAddedFile(field, file) {
      const oldFiles = this.getOldFiles(field)
      return !oldFiles.some((f) => f.id === file.id)
    }
  }
}
</script>

<style lang="scss" scoped>
.asset-version-diff {
  border: 1px solid var(--border);
  border-radius: 0.8em;
  overflow: hidden;
}

.diff-header {
  background: var(--background-alt);
  border-bottom: 1px solid var(--border);
}

.diff-column {
  flex: 1;
  padding: 0.8em 1em;
  min-width: 0;

  &.version-a {
    border-right: 1px solid var(--border);
  }
}

.version-label {
  display: flex;
  align-items: center;
  gap: 0.5em;
}

.version-number {
  font-weight: 700;
  font-size: 1em;
  color: var(--text-strong);
}

.version-meta {
  font-size: 0.85em;
  color: var(--text-alt);
}

.diff-empty {
  padding: 2em;
  text-align: center;
  color: var(--text-alt);
}

.diff-row {
  border-bottom: 1px solid var(--border);

  &:last-child {
    border-bottom: none;
  }
}

.diff-field-header {
  display: flex;
  align-items: center;
  gap: 0.5em;
  padding: 0.5em 1em;
  cursor: pointer;
  background: var(--background);
  transition: background 0.15s;

  &:hover {
    background: var(--background-hover);
  }
}

.field-name {
  font-weight: 600;
  font-size: 0.9em;
  color: var(--text-strong);
}

.change-badge {
  font-size: 0.75em;
  padding: 0.15em 0.5em;
  border-radius: 0.5em;
  font-weight: 500;

  &.added {
    background: #2d5a3d;
    color: #a3d9b1;
  }

  &.removed {
    background: #5a2d2d;
    color: #d9a3a3;
  }

  &.changed {
    background: #4a4a2d;
    color: #d9d9a3;
  }
}

.collapse-icon {
  margin-left: auto;
  font-size: 0.7em;
  color: var(--text-alt);
}

.diff-field-body {
  border-top: 1px solid var(--border);
}

// Text diff
.text-diff {
  font-size: 0.9em;
  line-height: 1.5;
  word-break: break-word;
  white-space: pre-wrap;

  &.old-value {
    background: rgba(90, 45, 45, 0.15);
    color: var(--text);
  }

  &.new-value {
    background: rgba(45, 90, 61, 0.15);
    color: var(--text);
  }
}

// Array diff
.array-diff {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4em;
}

.tag-chip {
  background: var(--background-alt);
  padding: 0.2em 0.6em;
  border-radius: 1em;
  font-size: 0.8em;
  color: var(--text);
  display: inline-flex;
  align-items: center;
  gap: 0.2em;

  &.added {
    background: #2d5a3d;
    color: #a3d9b1;
  }

  &.removed {
    background: #5a2d2d;
    color: #d9a3a3;
    text-decoration: line-through;
  }
}

.diff-indicator {
  font-weight: 700;
  font-size: 0.9em;
}

// JSON diff
.json-diff {
  font-family: monospace;
  font-size: 0.85em;
}

.json-row {
  padding: 0.15em 0;

  &.added {
    background: rgba(45, 90, 61, 0.15);
  }

  &.removed {
    background: rgba(90, 45, 45, 0.15);
    text-decoration: line-through;
  }

  &.changed {
    background: rgba(90, 90, 45, 0.15);
  }
}

.json-key {
  color: var(--text-alt);
  margin-right: 0.3em;
}

.json-value {
  color: var(--text);
}

// File diff
.file-diff {
  display: flex;
  flex-direction: column;
  gap: 0.4em;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 0.5em;
  padding: 0.3em;
  border-radius: 0.3em;

  &.added {
    background: rgba(45, 90, 61, 0.15);
  }

  &.removed {
    background: rgba(90, 45, 45, 0.15);
    opacity: 0.7;
  }
}

.file-thumb {
  width: 32px;
  height: 32px;
  border-radius: 0.2em;
  overflow: hidden;
  flex-shrink: 0;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

.file-name {
  font-size: 0.85em;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
