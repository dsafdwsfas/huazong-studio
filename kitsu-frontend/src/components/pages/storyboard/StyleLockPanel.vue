<template>
  <div class="style-lock-panel">
    <!-- Header -->
    <div class="panel-header">
      <div class="panel-title">
        <h3>
          <span class="title-icon">&#x1F3A8;</span>
          &#x98CE;&#x683C;&#x9501;&#x5B9A;
          <span class="project-name" v-if="projectName">
            &mdash; &#x9879;&#x76EE;: &#x300A;{{ projectName }}&#x300B;
          </span>
        </h3>
      </div>
      <button class="btn-back" @click="$emit('back')">
        <ArrowLeftIcon :size="16" />
        &#x8FD4;&#x56DE;&#x5206;&#x955C;
      </button>
    </div>

    <!-- Lock status bar -->
    <div class="lock-status-bar" v-if="lockedStyle">
      <LockIcon :size="14" />
      <span class="lock-info">
        &#x5DF2;&#x9501;&#x5B9A;
        <template v-if="lockedStyle.locked_at">
          &middot; {{ formatDate(lockedStyle.locked_at) }}
        </template>
        <template v-if="lockedStyle.locked_by">
          &middot; {{ lockedStyle.locked_by }}
        </template>
      </span>
    </div>

    <!-- Main content -->
    <div class="panel-body">
      <!-- Left: Reference images -->
      <div class="reference-section">
        <div class="section-header">
          <div class="section-label">
            &#x53C2;&#x8003;&#x56FE; ({{ referenceImages.length }}/10)
          </div>
        </div>

        <div class="image-grid" v-if="referenceImages.length">
          <div
            v-for="img in referenceImages"
            :key="img.id"
            class="image-card"
            :class="{ selected: selectedImageId === img.id }"
            @click="onSelectImage(img)"
          >
            <img
              :src="getImageUrl(img)"
              :alt="img.name || '&#x53C2;&#x8003;&#x56FE;'"
              class="image-thumb"
              @click.stop="onPreviewImage(img)"
            />
            <button
              class="btn-remove-image"
              @click.stop="$emit('remove-reference', { imageId: img.id })"
              title="&#x5220;&#x9664;"
            >
              <XIcon :size="12" />
            </button>
            <div class="image-label" v-if="img.name">
              {{ img.name }}
            </div>
            <div
              class="image-status"
              v-if="img.analysis_result"
              title="&#x5DF2;&#x5206;&#x6790;"
            >
              <CheckCircleIcon :size="12" />
            </div>
          </div>
        </div>

        <div class="empty-images" v-else>
          <ImageIcon :size="32" />
          <p>&#x6682;&#x65E0;&#x53C2;&#x8003;&#x56FE;&#xFF0C;&#x70B9;&#x51FB;&#x4E0B;&#x65B9;&#x6309;&#x94AE;&#x6DFB;&#x52A0;</p>
        </div>

        <button
          class="btn-add-image"
          @click="onAddReference"
          :disabled="referenceImages.length >= 10"
        >
          <PlusIcon :size="14" />
          &#x6DFB;&#x52A0;&#x53C2;&#x8003;&#x56FE;
        </button>
        <input
          ref="fileInput"
          type="file"
          accept="image/*"
          class="hidden-input"
          @change="onFileSelected"
        />
      </div>

      <!-- Right: Extraction results -->
      <div class="result-section">
        <div class="section-header">
          <div class="section-label">&#x63D0;&#x53D6;&#x7ED3;&#x679C;</div>
          <div class="view-toggle" v-if="referenceImages.length">
            <button
              :class="{ active: viewMode === 'aggregated' }"
              @click="viewMode = 'aggregated'"
            >
              &#x805A;&#x5408;
            </button>
            <button
              :class="{ active: viewMode === 'single' }"
              @click="viewMode = 'single'"
              :disabled="!selectedImageId"
            >
              &#x5355;&#x56FE;
            </button>
          </div>
        </div>

        <!-- Loading -->
        <div class="result-loading" v-if="isAnalyzing">
          <div class="spinner" />
          <span class="loading-text">&#x5206;&#x6790;&#x4E2D;...</span>
          <div class="pulse-bar">
            <div class="pulse-fill" />
          </div>
        </div>

        <!-- No images -->
        <div class="result-empty" v-else-if="!referenceImages.length">
          <PaletteIcon :size="32" />
          <p>&#x6DFB;&#x52A0;&#x53C2;&#x8003;&#x56FE;&#x540E;&#x53EF;&#x63D0;&#x53D6;&#x98CE;&#x683C;</p>
        </div>

        <!-- No analysis yet -->
        <div
          class="result-empty"
          v-else-if="!displayStyle && !isAnalyzing"
        >
          <SearchIcon :size="32" />
          <p>&#x70B9;&#x51FB;&ldquo;&#x91CD;&#x65B0;&#x5206;&#x6790;&rdquo;&#x5F00;&#x59CB;&#x63D0;&#x53D6;&#x98CE;&#x683C;</p>
        </div>

        <!-- Display style results -->
        <template v-else-if="displayStyle">
          <!-- Art style -->
          <div class="result-block" v-if="displayStyle.art_style">
            <div class="result-label">
              <span class="label-icon">&#x1F3A8;</span>
              &#x827A;&#x672F;&#x98CE;&#x683C;
            </div>
            <div class="result-value">{{ displayStyle.art_style }}</div>
          </div>

          <!-- Color tone -->
          <div class="result-block" v-if="displayStyle.color_tone">
            <div class="result-label">
              <span class="label-icon">&#x1F308;</span>
              &#x8272;&#x8C03;
            </div>
            <div class="result-value">{{ displayStyle.color_tone }}</div>
          </div>

          <!-- Dominant colors -->
          <div
            class="result-block"
            v-if="displayStyle.dominant_colors && displayStyle.dominant_colors.length"
          >
            <div class="result-label">
              <span class="label-icon">&#x1F3A8;</span>
              &#x4E3B;&#x8272;&#x8C03;
            </div>
            <div class="color-swatches">
              <div
                v-for="(color, idx) in displayStyle.dominant_colors"
                :key="idx"
                class="color-swatch"
                :title="color"
              >
                <span class="swatch-block" :style="{ background: color }" />
                <span class="swatch-hex">{{ color }}</span>
              </div>
            </div>
          </div>

          <!-- Lighting -->
          <div class="result-block" v-if="displayStyle.lighting">
            <div class="result-label">
              <span class="label-icon">&#x1F4A1;</span>
              &#x5149;&#x5F71;
            </div>
            <div class="result-value">{{ displayStyle.lighting }}</div>
          </div>

          <!-- Composition -->
          <div class="result-block" v-if="displayStyle.composition">
            <div class="result-label">
              <span class="label-icon">&#x1F4D0;</span>
              &#x6784;&#x56FE;
            </div>
            <div class="result-value">{{ displayStyle.composition }}</div>
          </div>

          <!-- Mood -->
          <div class="result-block" v-if="displayStyle.mood">
            <div class="result-label">
              <span class="label-icon">&#x1F60A;</span>
              &#x6C1B;&#x56F4;
            </div>
            <div class="result-value">{{ displayStyle.mood }}</div>
          </div>

          <!-- Camera angle -->
          <div class="result-block" v-if="displayStyle.camera_angle">
            <div class="result-label">
              <span class="label-icon">&#x1F4F7;</span>
              &#x955C;&#x5934;
            </div>
            <div class="result-value">{{ displayStyle.camera_angle }}</div>
          </div>

          <!-- Keywords -->
          <div
            class="result-block"
            v-if="displayStyle.style_keywords_cn && displayStyle.style_keywords_cn.length"
          >
            <div class="result-label">&#x5173;&#x952E;&#x8BCD;</div>
            <div class="keyword-chips">
              <span
                v-for="(kw, idx) in displayStyle.style_keywords_cn"
                :key="idx"
                class="chip"
              >
                {{ kw.text || kw }}
                <span class="chip-count" v-if="kw.count">({{ kw.count }})</span>
              </span>
            </div>
          </div>

          <!-- Reference artists -->
          <div
            class="result-block"
            v-if="displayStyle.reference_artists && displayStyle.reference_artists.length"
          >
            <div class="result-label">&#x53C2;&#x8003;&#x827A;&#x672F;&#x5BB6;</div>
            <div class="artists-text">
              {{ displayStyle.reference_artists.join(' &middot; ') }}
            </div>
          </div>

          <!-- Description -->
          <div class="result-block" v-if="displayStyle.description">
            <div class="result-label">&#x63CF;&#x8FF0;</div>
            <p class="description-text">{{ displayStyle.description }}</p>
          </div>
        </template>
      </div>
    </div>

    <!-- Footer actions -->
    <div class="panel-footer">
      <button
        v-if="!lockedStyle"
        class="btn-action btn-lock"
        :disabled="!aggregatedStyle || isLocking"
        @click="onLockStyle"
      >
        <LockIcon :size="14" />
        {{ isLocking ? '&#x9501;&#x5B9A;&#x4E2D;...' : '&#x9501;&#x5B9A;&#x6B64;&#x98CE;&#x683C;' }}
      </button>
      <button
        v-else
        class="btn-action btn-unlock"
        @click="onUnlockStyle"
      >
        <UnlockIcon :size="14" />
        &#x5DF2;&#x9501;&#x5B9A; &mdash; &#x70B9;&#x51FB;&#x89E3;&#x9501;
      </button>

      <button
        class="btn-action btn-export"
        @click="$emit('export-report')"
        :disabled="!aggregatedStyle && !lockedStyle"
      >
        <ClipboardListIcon :size="14" />
        &#x5BFC;&#x51FA;&#x98CE;&#x683C;&#x62A5;&#x544A;
      </button>

      <button
        class="btn-action btn-reanalyze"
        @click="onAnalyzeAll"
        :disabled="!referenceImages.length || isAnalyzing"
      >
        <RefreshCwIcon :size="14" />
        &#x91CD;&#x65B0;&#x5206;&#x6790;
      </button>

      <button
        class="btn-action btn-templates"
        @click="showTemplateLibrary = true"
      >
        <BookmarkIcon :size="14" />
        &#x6A21;&#x677F;&#x5E93;
      </button>
    </div>

    <!-- Image preview modal -->
    <div class="preview-overlay" v-if="showPreview" @click="showPreview = false">
      <div class="preview-container" @click.stop>
        <img :src="previewUrl" class="preview-image" />
        <button class="btn-close-preview" @click="showPreview = false">
          <XIcon :size="20" />
        </button>
      </div>
    </div>

    <!-- Template Library Modal -->
    <StyleTemplateLibrary
      :active="showTemplateLibrary"
      :project-id="projectId"
      :current-style="aggregatedStyle || (lockedStyle ? lockedStyle.style : null)"
      @close="showTemplateLibrary = false"
      @apply="onTemplateApplied"
      @saved="onTemplateSaved"
    />
  </div>
</template>

<script>
import {
  ArrowLeftIcon,
  BookmarkIcon,
  CheckCircleIcon,
  ClipboardListIcon,
  ImageIcon,
  LockIcon,
  PaletteIcon,
  PlusIcon,
  RefreshCwIcon,
  SearchIcon,
  UnlockIcon,
  XIcon
} from 'lucide-vue-next'
import StyleTemplateLibrary from '@/components/pages/storyboard/StyleTemplateLibrary.vue'

export default {
  name: 'StyleLockPanel',

  components: {
    ArrowLeftIcon,
    BookmarkIcon,
    CheckCircleIcon,
    ClipboardListIcon,
    ImageIcon,
    LockIcon,
    PaletteIcon,
    StyleTemplateLibrary,
    PlusIcon,
    RefreshCwIcon,
    SearchIcon,
    UnlockIcon,
    XIcon
  },

  props: {
    projectId: {
      type: String,
      required: true
    },
    projectName: {
      type: String,
      default: ''
    },
    lockedStyle: {
      type: Object,
      default: null
    },
    referenceImages: {
      type: Array,
      default: () => []
    }
  },

  emits: [
    'back',
    'lock-style',
    'unlock-style',
    'add-reference',
    'remove-reference',
    'analyze-reference',
    'analyze-all',
    'export-report'
  ],

  data() {
    return {
      selectedImageId: null,
      aggregatedStyle: null,
      isAnalyzing: false,
      isLocking: false,
      showPreview: false,
      previewUrl: '',
      viewMode: 'aggregated',
      showTemplateLibrary: false
    }
  },

  computed: {
    displayStyle() {
      if (this.viewMode === 'single' && this.selectedImageId) {
        const img = this.referenceImages.find(
          i => i.id === this.selectedImageId
        )
        if (img && img.analysis_result) {
          return img.analysis_result.result || img.analysis_result
        }
        return null
      }
      return this.aggregatedStyle
    },

    analyzedImages() {
      return this.referenceImages.filter(
        img => img.analysis_result
      )
    }
  },

  watch: {
    referenceImages: {
      handler() {
        this.computeAggregatedStyle()
      },
      deep: true,
      immediate: true
    }
  },

  methods: {
    computeAggregatedStyle() {
      const images = this.analyzedImages
      if (!images.length) {
        this.aggregatedStyle = null
        return
      }
      this.aggregatedStyle = this.aggregateStyles(images)
    },

    aggregateStyles(images) {
      const artStyles = []
      const colorTones = []
      const lightings = []
      const compositions = []
      const moods = []
      const cameraAngles = []
      const allColors = []
      const keywordMap = {}
      const artists = []
      const descriptions = []

      images.forEach(img => {
        const r = img.analysis_result?.result || img.analysis_result
        if (!r) return

        if (r.art_style) artStyles.push(r.art_style)
        if (r.color_tone) colorTones.push(r.color_tone)
        if (r.lighting) lightings.push(r.lighting)
        if (r.composition) compositions.push(r.composition)
        if (r.mood) moods.push(r.mood)
        if (r.camera_angle) cameraAngles.push(r.camera_angle)
        if (r.description) descriptions.push(r.description)

        if (r.dominant_colors) {
          r.dominant_colors.forEach(c => {
            if (!allColors.includes(c)) allColors.push(c)
          })
        }

        if (r.style_keywords_cn) {
          r.style_keywords_cn.forEach(kw => {
            const text = typeof kw === 'string' ? kw : kw.text || kw
            keywordMap[text] = (keywordMap[text] || 0) + 1
          })
        }

        if (r.reference_artists) {
          r.reference_artists.forEach(a => {
            if (!artists.includes(a)) artists.push(a)
          })
        }
      })

      const sortedKeywords = Object.entries(keywordMap)
        .sort((a, b) => b[1] - a[1])
        .map(([text, count]) => ({ text, count }))

      return {
        art_style: this.majorityVote(artStyles),
        color_tone: this.majorityVote(colorTones),
        lighting: this.majorityVote(lightings),
        composition: this.majorityVote(compositions),
        mood: this.majorityVote(moods),
        camera_angle: this.majorityVote(cameraAngles),
        dominant_colors: allColors.slice(0, 8),
        style_keywords_cn: sortedKeywords,
        reference_artists: artists,
        description: descriptions[0] || ''
      }
    },

    majorityVote(arr) {
      if (!arr.length) return ''
      const counts = {}
      arr.forEach(v => {
        counts[v] = (counts[v] || 0) + 1
      })
      let max = 0
      let winner = ''
      Object.entries(counts).forEach(([val, count]) => {
        if (count > max) {
          max = count
          winner = val
        }
      })
      return winner
    },

    onSelectImage(img) {
      this.selectedImageId =
        this.selectedImageId === img.id ? null : img.id
    },

    onPreviewImage(img) {
      this.previewUrl = this.getImageUrl(img)
      this.showPreview = true
    },

    getImageUrl(img) {
      if (img.url) return img.url
      if (img.preview_file_id) {
        return `/api/pictures/originals/preview-files/${img.preview_file_id}.png`
      }
      return ''
    },

    onAddReference() {
      this.$refs.fileInput.click()
    },

    onFileSelected(e) {
      const file = e.target.files[0]
      if (file) {
        this.$emit('add-reference', { file })
      }
      e.target.value = ''
    },

    onLockStyle() {
      if (!this.aggregatedStyle) return
      this.isLocking = true
      const imageIds = this.referenceImages.map(i => i.id)
      this.$emit('lock-style', {
        style: this.aggregatedStyle,
        referenceImageIds: imageIds
      })
      setTimeout(() => {
        this.isLocking = false
      }, 1000)
    },

    onUnlockStyle() {
      this.$emit('unlock-style')
    },

    onAnalyzeAll() {
      this.isAnalyzing = true
      this.$emit('analyze-all')
      setTimeout(() => {
        this.isAnalyzing = false
      }, 2000)
    },

    onTemplateApplied(tpl) {
      // Reload locked style after template applied
      this.$emit('back')
    },

    onTemplateSaved() {
      // Template saved notification (optional)
    },

    formatDate(isoString) {
      if (!isoString) return ''
      const d = new Date(isoString)
      const y = d.getFullYear()
      const m = String(d.getMonth() + 1).padStart(2, '0')
      const day = String(d.getDate()).padStart(2, '0')
      const h = String(d.getHours()).padStart(2, '0')
      const min = String(d.getMinutes()).padStart(2, '0')
      return `${y}-${m}-${day} ${h}:${min}`
    }
  }
}
</script>

<style lang="scss" scoped>
.style-lock-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--background);
  color: var(--text);
}

// Header
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.panel-title {
  flex: 1;
  min-width: 0;

  h3 {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 6px;
  }
}

.title-icon {
  font-size: 1.1rem;
}

.project-name {
  font-weight: 400;
  color: var(--text-alt);
  font-size: 0.9rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.btn-back {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: none;
  color: var(--text);
  font-size: 0.8rem;
  cursor: pointer;
  flex-shrink: 0;

  &:hover {
    background: var(--background-hover);
  }
}

// Lock status bar
.lock-status-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 20px;
  background: linear-gradient(135deg, rgba(16, 172, 132, 0.15), rgba(16, 172, 132, 0.05));
  border-bottom: 1px solid rgba(16, 172, 132, 0.2);
  color: #10ac84;
  font-size: 0.8rem;
  font-weight: 500;
  flex-shrink: 0;
}

.lock-info {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

// Body layout
.panel-body {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

// Left: reference images
.reference-section {
  width: 40%;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border);
  padding: 16px;
  overflow-y: auto;
}

// Right: results
.result-section {
  width: 60%;
  display: flex;
  flex-direction: column;
  padding: 16px;
  overflow-y: auto;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  flex-shrink: 0;
}

.section-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-alt);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

// View toggle
.view-toggle {
  display: flex;
  gap: 0;
  border: 1px solid var(--border);
  border-radius: 6px;
  overflow: hidden;

  button {
    padding: 3px 10px;
    border: none;
    background: none;
    color: var(--text-alt);
    font-size: 0.7rem;
    cursor: pointer;

    &.active {
      background: var(--color-primary, #0078ff);
      color: #fff;
    }

    &:disabled {
      opacity: 0.4;
      cursor: default;
    }
  }
}

// Image grid
.image-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-bottom: 12px;
}

.image-card {
  position: relative;
  aspect-ratio: 1;
  border-radius: 6px;
  overflow: hidden;
  border: 2px solid transparent;
  cursor: pointer;
  transition: border-color 0.15s;

  &:hover {
    border-color: var(--border);

    .btn-remove-image {
      opacity: 1;
    }
  }

  &.selected {
    border-color: var(--color-primary, #0078ff);
  }
}

.image-thumb {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.btn-remove-image {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: none;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.image-label {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 2px 4px;
  background: rgba(0, 0, 0, 0.5);
  color: #fff;
  font-size: 0.6rem;
  text-overflow: ellipsis;
  overflow: hidden;
  white-space: nowrap;
}

.image-status {
  position: absolute;
  top: 4px;
  left: 4px;
  color: #10ac84;
}

// Empty images
.empty-images {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 32px 16px;
  color: var(--text-alt);
  text-align: center;

  p {
    font-size: 0.8rem;
    margin: 0;
    line-height: 1.4;
  }
}

.btn-add-image {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  width: 100%;
  padding: 8px;
  border: 2px dashed var(--border);
  border-radius: 6px;
  background: none;
  color: var(--text-alt);
  font-size: 0.8rem;
  cursor: pointer;
  margin-top: auto;

  &:hover:not(:disabled) {
    border-color: var(--color-primary, #0078ff);
    color: var(--color-primary, #0078ff);
  }

  &:disabled {
    opacity: 0.4;
    cursor: default;
  }
}

.hidden-input {
  display: none;
}

// Result blocks
.result-block {
  margin-bottom: 16px;
}

.result-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-alt);
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.label-icon {
  font-size: 0.85rem;
}

.result-value {
  font-size: 0.9rem;
  font-weight: 500;
}

// Color swatches
.color-swatches {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.color-swatch {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.swatch-block {
  width: 28px;
  height: 28px;
  border-radius: 4px;
  border: 1px solid var(--border);
}

.swatch-hex {
  font-size: 0.6rem;
  color: var(--text-alt);
  font-family: monospace;
}

// Keyword chips
.keyword-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.chip {
  padding: 3px 10px;
  border-radius: 12px;
  background: var(--background-alt);
  font-size: 0.75rem;
  color: var(--text);
  white-space: nowrap;
}

.chip-count {
  font-size: 0.65rem;
  color: var(--text-alt);
  margin-left: 2px;
}

// Artists
.artists-text {
  font-size: 0.85rem;
  line-height: 1.4;
}

// Description
.description-text {
  font-size: 0.85rem;
  margin: 0;
  line-height: 1.5;
  color: var(--text);
}

// Loading
.result-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 32px 16px;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--border);
  border-top-color: var(--color-primary, #0078ff);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  font-size: 0.85rem;
  color: var(--text-alt);
}

.pulse-bar {
  width: 80%;
  height: 4px;
  background: var(--background-alt);
  border-radius: 2px;
  overflow: hidden;
}

.pulse-fill {
  width: 40%;
  height: 100%;
  background: var(--color-primary, #0078ff);
  border-radius: 2px;
  animation: pulse-slide 1.5s ease-in-out infinite;
}

@keyframes pulse-slide {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(350%); }
}

// Empty result
.result-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 32px 16px;
  color: var(--text-alt);
  text-align: center;

  p {
    font-size: 0.85rem;
    margin: 0;
    line-height: 1.4;
  }
}

// Footer
.panel-footer {
  display: flex;
  gap: 8px;
  padding: 12px 20px;
  border-top: 1px solid var(--border);
  flex-shrink: 0;
}

.btn-action {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 14px;
  border: none;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.15s;
  color: #fff;

  &:hover:not(:disabled) {
    opacity: 0.85;
  }

  &:disabled {
    opacity: 0.4;
    cursor: default;
  }
}

.btn-lock {
  background: var(--color-primary, #0078ff);
}

.btn-unlock {
  background: #10ac84;
}

.btn-export {
  background: #6c5ce7;
}

.btn-reanalyze {
  background: #636e72;
}

// Preview overlay
.preview-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.preview-container {
  position: relative;
  max-width: 90vw;
  max-height: 90vh;
}

.preview-image {
  max-width: 100%;
  max-height: 90vh;
  object-fit: contain;
  border-radius: 4px;
}

.btn-close-preview {
  position: absolute;
  top: -32px;
  right: 0;
  background: none;
  border: none;
  color: #fff;
  cursor: pointer;
  padding: 4px;

  &:hover {
    opacity: 0.8;
  }
}
</style>
