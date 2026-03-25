<template>
  <div class="style-analysis-panel" v-if="active">
    <div class="panel-header">
      <div class="panel-title">
        <h4>AI 风格分析</h4>
        <span class="shot-label" v-if="shot">{{ shot.name }}</span>
      </div>
      <button class="btn-close" @click="$emit('close')">
        <XIcon :size="16" />
      </button>
    </div>

    <!-- Actions -->
    <div class="panel-section">
      <div class="action-buttons">
        <button
          v-if="!analysisResult && !isAnalyzing"
          class="btn-action btn-analyze"
          @click="onAnalyze"
          :disabled="!shot || !shot.preview_file_id"
        >
          <SearchIcon :size="14" />
          开始分析
        </button>
        <button
          v-if="analysisResult && !isAnalyzing"
          class="btn-action btn-reanalyze"
          @click="onReanalyze"
        >
          <RefreshCwIcon :size="14" />
          重新分析
        </button>
      </div>
    </div>

    <!-- Loading state -->
    <div class="panel-section section-loading" v-if="isAnalyzing">
      <div class="loading-indicator">
        <div class="spinner" />
        <span class="loading-text">分析中...</span>
      </div>
      <div class="pulse-bar">
        <div class="pulse-fill" />
      </div>
    </div>

    <!-- Error state -->
    <div class="panel-section section-error" v-else-if="hasError">
      <div class="error-content">
        <AlertCircleIcon :size="20" />
        <p class="error-message">{{ errorMessage }}</p>
        <button class="btn-action btn-retry" @click="onAnalyze">
          <RefreshCwIcon :size="14" />
          重试
        </button>
      </div>
    </div>

    <!-- No preview state -->
    <div
      class="panel-section section-empty"
      v-else-if="shot && !shot.preview_file_id && !analysisResult"
    >
      <div class="empty-content">
        <ImageIcon :size="32" />
        <p>该分镜暂无预览图，无法进行风格分析</p>
      </div>
    </div>

    <!-- Empty state (has preview but not analyzed) -->
    <div
      class="panel-section section-empty"
      v-else-if="!analysisResult && !isAnalyzing"
    >
      <div class="empty-content">
        <PaletteIcon :size="32" />
        <p>点击"开始分析"使用 AI 识别画面风格</p>
      </div>
    </div>

    <!-- Analysis result -->
    <template v-else-if="analysisResult">
      <!-- Style attributes -->
      <div class="panel-section">
        <div class="section-label">风格属性</div>
        <div class="attribute-list">
          <div class="attribute-row" v-if="analysisResult.art_style">
            <span class="attr-icon">🎨</span>
            <span class="attr-label">艺术风格</span>
            <span class="attr-value">{{ analysisResult.art_style }}</span>
          </div>
          <div class="attribute-row" v-if="analysisResult.color_tone">
            <span class="attr-icon">🌈</span>
            <span class="attr-label">色调</span>
            <span class="attr-value">{{ analysisResult.color_tone }}</span>
          </div>
          <div class="attribute-row" v-if="analysisResult.lighting">
            <span class="attr-icon">💡</span>
            <span class="attr-label">光影</span>
            <span class="attr-value">{{ analysisResult.lighting }}</span>
          </div>
          <div class="attribute-row" v-if="analysisResult.composition">
            <span class="attr-icon">📐</span>
            <span class="attr-label">构图</span>
            <span class="attr-value">{{ analysisResult.composition }}</span>
          </div>
          <div class="attribute-row" v-if="analysisResult.camera_angle">
            <span class="attr-icon">📷</span>
            <span class="attr-label">镜头</span>
            <span class="attr-value">{{ analysisResult.camera_angle }}</span>
          </div>
          <div class="attribute-row" v-if="analysisResult.mood">
            <span class="attr-icon">😊</span>
            <span class="attr-label">氛围</span>
            <span class="attr-value">{{ analysisResult.mood }}</span>
          </div>
        </div>
      </div>

      <!-- Dominant colors -->
      <div
        class="panel-section"
        v-if="analysisResult.dominant_colors && analysisResult.dominant_colors.length"
      >
        <div class="section-label">主色调</div>
        <div class="color-swatches">
          <div
            v-for="(color, idx) in analysisResult.dominant_colors"
            :key="idx"
            class="color-swatch"
            :title="color"
          >
            <span class="swatch-block" :style="{ background: color }" />
            <span class="swatch-hex">{{ color }}</span>
          </div>
        </div>
      </div>

      <!-- Style keywords CN -->
      <div
        class="panel-section"
        v-if="keywordPairs.length || (analysisResult.style_keywords_cn && analysisResult.style_keywords_cn.length)"
      >
        <div class="section-label">风格关键词</div>
        <!-- Bilingual pairs (3.3 enhanced) -->
        <div v-if="keywordPairs.length" class="keyword-chips">
          <span
            v-for="(pair, idx) in keywordPairs"
            :key="idx"
            class="chip chip-bilingual"
            :class="{ 'chip-glossary': pair.source === 'glossary', 'chip-ai': pair.source === 'gemini' }"
            :title="pair.en + (pair.source ? ' (' + pair.source + ')' : '')"
          >
            {{ pair.cn }}
            <span class="chip-en">{{ pair.en }}</span>
          </span>
        </div>
        <!-- Fallback: CN only -->
        <div v-else class="keyword-chips">
          <span
            v-for="(kw, idx) in analysisResult.style_keywords_cn"
            :key="idx"
            class="chip"
          >
            {{ kw }}
          </span>
        </div>
      </div>

      <!-- Reference artists -->
      <div
        class="panel-section"
        v-if="analysisResult.reference_artists && analysisResult.reference_artists.length"
      >
        <div class="section-label">参考艺术家</div>
        <div class="artists-text">
          {{ analysisResult.reference_artists.join(' · ') }}
        </div>
      </div>

      <!-- Description -->
      <div class="panel-section" v-if="analysisResult.description">
        <div class="section-label">描述</div>
        <p class="description-text">{{ analysisResult.description }}</p>
      </div>

      <!-- Technical metadata (3.2) -->
      <div
        class="panel-section"
        v-if="analysisResult.technical"
      >
        <div class="section-label">技术信息</div>
        <div class="tech-grid">
          <div class="tech-item" v-if="analysisResult.technical.resolution">
            <span class="tech-label">分辨率</span>
            <span class="tech-value">{{ analysisResult.technical.resolution }}</span>
          </div>
          <div class="tech-item" v-if="analysisResult.technical.aspect_ratio">
            <span class="tech-label">比例</span>
            <span class="tech-value">{{ analysisResult.technical.aspect_ratio }}</span>
          </div>
          <div class="tech-item" v-if="analysisResult.technical.format">
            <span class="tech-label">格式</span>
            <span class="tech-value">{{ analysisResult.technical.format }}</span>
          </div>
          <div class="tech-item" v-if="analysisResult.technical.color_mode">
            <span class="tech-label">色彩模式</span>
            <span class="tech-value">{{ analysisResult.technical.color_mode }}</span>
          </div>
          <div class="tech-item" v-if="analysisResult.technical.file_size_human">
            <span class="tech-label">文件大小</span>
            <span class="tech-value">{{ analysisResult.technical.file_size_human }}</span>
          </div>
          <div class="tech-item" v-if="analysisResult.technical.dpi">
            <span class="tech-label">DPI</span>
            <span class="tech-value">{{ analysisResult.technical.dpi }}</span>
          </div>
          <div class="tech-item" v-if="analysisResult.technical.bit_depth">
            <span class="tech-label">位深</span>
            <span class="tech-value">{{ analysisResult.technical.bit_depth }}bit</span>
          </div>
          <div
            class="tech-item"
            v-if="analysisResult.technical.has_alpha !== undefined"
          >
            <span class="tech-label">透明通道</span>
            <span class="tech-value">{{ analysisResult.technical.has_alpha ? '是' : '否' }}</span>
          </div>
        </div>
        <!-- EXIF data (photos only) -->
        <div
          class="exif-section"
          v-if="analysisResult.technical.exif && Object.keys(analysisResult.technical.exif).length"
        >
          <div class="section-label">EXIF 信息</div>
          <div class="tech-grid">
            <div
              class="tech-item"
              v-for="(val, key) in analysisResult.technical.exif"
              :key="key"
            >
              <span class="tech-label">{{ exifLabel(key) }}</span>
              <span class="tech-value">{{ val }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Normalized keywords badge (3.2) -->
      <div
        class="panel-section"
        v-if="analysisResult.normalized && analysisResult.metadata_version"
      >
        <div class="meta-badge normalized-badge">
          元数据 v{{ analysisResult.metadata_version }} · 已归一化
        </div>
      </div>

      <!-- Style consistency check (3.9) -->
      <div class="panel-section" v-if="consistencyResult && consistencyResult.score >= 0">
        <div class="section-label">风格一致性</div>
        <div class="consistency-score" :class="consistencyClass">
          <span class="score-num">{{ consistencyResult.score }}</span>
          <span class="score-label">/ 100</span>
        </div>
        <div class="consistency-details" v-if="consistencyResult.mismatches && consistencyResult.mismatches.length">
          <div
            v-for="(m, idx) in consistencyResult.mismatches"
            :key="idx"
            class="mismatch-item"
            :class="'severity-' + m.severity"
          >
            <span class="mismatch-dim">{{ m.label }}</span>
            <span class="mismatch-diff">{{ m.locked }} → {{ m.actual }}</span>
          </div>
        </div>
        <div class="consistency-stats">
          <span>色彩相似度: {{ consistencyResult.color_similarity }}%</span>
          <span>关键词重叠: {{ Math.round((consistencyResult.keyword_overlap || 0) * 100) }}%</span>
        </div>
      </div>

      <!-- Meta info -->
      <div class="panel-section section-meta">
        <div class="meta-row" v-if="analysisResult.analyzed_at">
          <span class="meta-label">分析时间</span>
          <span class="meta-value">{{ formatDate(analysisResult.analyzed_at) }}</span>
        </div>
        <div class="meta-row" v-if="analysisResult.model">
          <span class="meta-label">模型</span>
          <span class="meta-value">{{ analysisResult.model }}</span>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import {
  AlertCircleIcon,
  ImageIcon,
  PaletteIcon,
  RefreshCwIcon,
  SearchIcon,
  XIcon
} from 'lucide-vue-next'

export default {
  name: 'StyleAnalysisPanel',

  components: {
    AlertCircleIcon,
    ImageIcon,
    PaletteIcon,
    RefreshCwIcon,
    SearchIcon,
    XIcon
  },

  props: {
    active: {
      type: Boolean,
      default: false
    },
    projectId: {
      type: String,
      required: true
    },
    shot: {
      type: Object,
      default: null
    },
    analysisResult: {
      type: Object,
      default: null
    },
    isAnalyzing: {
      type: Boolean,
      default: false
    }
  },

  emits: ['close', 'analyze', 'reanalyze'],

  data() {
    return {
      hasError: false,
      consistencyResult: null,
      errorMessage: ''
    }
  },

  watch: {
    'shot.id'() {
      this.hasError = false
      this.errorMessage = ''
    },
    analysisResult(val) {
      if (val) {
        this.hasError = false
        this.errorMessage = ''
        this.loadConsistency()
      }
    },
    isAnalyzing(val) {
      if (val) {
        this.hasError = false
        this.errorMessage = ''
      }
    }
  },

  computed: {
    consistencyClass() {
      if (!this.consistencyResult) return ''
      const s = this.consistencyResult.score
      if (s >= 80) return 'score-high'
      if (s >= 50) return 'score-medium'
      return 'score-low'
    },

    keywordPairs() {
      if (!this.analysisResult) return []
      // Prefer keyword_pairs from backend (3.3 enriched)
      const result = this.analysisResult.result || this.analysisResult
      if (result.keyword_pairs && result.keyword_pairs.length) {
        return result.keyword_pairs
      }
      return []
    }
  },

  methods: {
    onAnalyze() {
      if (!this.shot?.id) return
      this.hasError = false
      this.$emit('analyze', { shotId: this.shot.id })
    },

    onReanalyze() {
      if (!this.shot?.id) return
      this.hasError = false
      this.$emit('reanalyze', { shotId: this.shot.id })
    },

    setError(message) {
      this.hasError = true
      this.errorMessage = message || '分析失败，请重试'
    },

    async loadConsistency() {
      if (!this.shot || !this.projectId) return
      try {
        this.consistencyResult = await this.$store.dispatch('checkStyleConsistency', {
          projectId: this.projectId,
          shotId: this.shot.id
        })
      } catch {
        this.consistencyResult = null
      }
    },

    exifLabel(key) {
      const labels = {
        camera: '相机',
        lens: '镜头',
        iso: 'ISO',
        shutter_speed: '快门',
        aperture: '光圈',
        focal_length: '焦距',
        date_taken: '拍摄时间'
      }
      return labels[key] || key
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
.style-analysis-panel {
  width: 360px;
  border-left: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--background);
  flex-shrink: 0;
  overflow-y: auto;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.panel-title {
  flex: 1;
  min-width: 0;

  h4 {
    margin: 0;
    font-size: 0.9rem;
    font-weight: 600;
  }

  .shot-label {
    font-size: 0.75rem;
    color: var(--text-alt);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    display: block;
    margin-top: 2px;
  }
}

.btn-close {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-alt);
  padding: 4px;
  border-radius: 4px;
  flex-shrink: 0;

  &:hover {
    background: var(--background-hover);
  }
}

.panel-section {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
}

.section-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-alt);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

// Action buttons
.action-buttons {
  display: flex;
  gap: 8px;
}

.btn-action {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
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

.btn-analyze {
  background: var(--color-primary, #0078ff);
}

.btn-reanalyze {
  background: #6c5ce7;
}

.btn-retry {
  background: #ff9f43;
  margin-top: 8px;
}

// Loading state
.section-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 24px 16px;
}

.loading-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
}

.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid var(--border);
  border-top-color: var(--color-primary, #0078ff);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-text {
  font-size: 0.85rem;
  color: var(--text-alt);
}

.pulse-bar {
  width: 100%;
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
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(350%);
  }
}

// Error state
.section-error {
  padding: 24px 16px;
}

.error-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #e17055;
  text-align: center;

  .error-message {
    font-size: 0.85rem;
    margin: 0;
    color: var(--text);
  }
}

// Empty state
.section-empty {
  padding: 32px 16px;
}

.empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: var(--text-alt);
  text-align: center;

  p {
    font-size: 0.85rem;
    margin: 0;
    line-height: 1.4;
  }
}

// Style attributes
.attribute-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.attribute-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
}

.attr-icon {
  flex-shrink: 0;
  width: 20px;
  text-align: center;
}

.attr-label {
  color: var(--text-alt);
  flex-shrink: 0;
  width: 60px;
  font-size: 0.8rem;
}

.attr-value {
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
  width: 24px;
  height: 24px;
  border-radius: 3px;
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
  padding: 2px 8px;
  border-radius: 12px;
  background: var(--background-alt);
  font-size: 0.75rem;
  color: var(--text);
  white-space: nowrap;
}

.chip-bilingual {
  display: inline-flex;
  align-items: baseline;
  gap: 4px;
}

.chip-en {
  font-size: 0.6rem;
  color: var(--text-alt);
  opacity: 0.7;
}

.chip-glossary {
  border-left: 2px solid #10ac84;
}

.chip-ai {
  border-left: 2px solid #0abde3;
}

// EN keywords
.en-keywords {
  font-size: 0.75rem;
  color: var(--text-alt);
  line-height: 1.4;
}

// Artists
.artists-text {
  font-size: 0.85rem;
  color: var(--text);
  line-height: 1.4;
}

// Description
.description-text {
  font-size: 0.85rem;
  color: var(--text);
  margin: 0;
  line-height: 1.5;
}

// Meta info
.section-meta {
  flex-shrink: 0;
}

.meta-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.75rem;

  & + & {
    margin-top: 4px;
  }
}

.meta-label {
  color: var(--text-alt);
}

.meta-value {
  color: var(--text);
  font-family: monospace;
  font-size: 0.7rem;
}

.tech-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}

.tech-item {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.tech-label {
  font-size: 0.65rem;
  color: var(--text-alt);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.tech-value {
  font-size: 0.75rem;
  color: var(--text);
  font-family: monospace;
}

.exif-section {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed var(--border);
}

.consistency-score {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 8px;

  .score-num { font-size: 1.5rem; font-weight: 700; }
  .score-label { font-size: 0.75rem; color: var(--text-alt); }

  &.score-high .score-num { color: #10ac84; }
  &.score-medium .score-num { color: #ff9f43; }
  &.score-low .score-num { color: #ff3860; }
}

.consistency-details { margin-bottom: 8px; }

.mismatch-item {
  display: flex;
  justify-content: space-between;
  padding: 3px 0;
  font-size: 0.75rem;
  border-bottom: 1px dashed var(--border);

  &.severity-high { color: #ff3860; }
  &.severity-medium { color: #ff9f43; }
  &.severity-low { color: var(--text-alt); }
}

.mismatch-dim { font-weight: 600; }
.mismatch-diff { font-family: monospace; }

.consistency-stats {
  display: flex;
  gap: 16px;
  font-size: 0.7rem;
  color: var(--text-alt);
}

.normalized-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 8px;
  font-size: 0.65rem;
  background: rgba(16, 172, 132, 0.1);
  color: #10ac84;
  border: 1px solid rgba(16, 172, 132, 0.2);
}
</style>
