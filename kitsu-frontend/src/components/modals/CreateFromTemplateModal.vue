<template>
  <div
    class="modal"
    :class="{ 'is-active': active }"
    @keyup.esc="$emit('cancel')"
  >
    <div class="modal-background" @click="$emit('cancel')"></div>
    <div class="modal-content">
      <div class="box">
        <h2 class="subtitle">从模板创建项目</h2>

        <div v-if="isLoadingTemplates" class="has-text-centered">
          <spinner />
        </div>

        <div v-else-if="templates.length === 0" class="empty-state">
          <p>暂无项目模板。请先在项目列表中将现有项目保存为模板。</p>
        </div>

        <div v-else>
          <!-- Template selection -->
          <div class="field">
            <label class="label">选择模板</label>
            <div class="control">
              <div class="select is-fullwidth">
                <select v-model="selectedTemplateId">
                  <option value="">请选择...</option>
                  <option
                    v-for="t in templates"
                    :key="t.id"
                    :value="t.id"
                  >
                    {{ t.name }}
                    ({{ t.production_type }} / {{ t.production_style }})
                  </option>
                </select>
              </div>
            </div>
          </div>

          <!-- Template info -->
          <div v-if="selectedTemplate" class="template-info">
            <p class="template-desc" v-if="selectedTemplate.description">
              {{ selectedTemplate.description }}
            </p>
            <div class="template-meta">
              <span class="tag">{{ selectedTemplate.production_type }}</span>
              <span class="tag">{{ selectedTemplate.production_style }}</span>
              <span class="tag">{{ selectedTemplate.fps }} fps</span>
              <span class="tag">{{ selectedTemplate.resolution }}</span>
            </div>
          </div>

          <!-- Project name -->
          <div class="field" v-if="selectedTemplateId">
            <label class="label">项目名称</label>
            <div class="control">
              <input
                class="input"
                type="text"
                v-model="projectName"
                placeholder="输入新项目名称"
                @keyup.enter="confirm"
                ref="nameInput"
              />
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button class="button" @click="$emit('cancel')">取消</button>
          <button
            class="button is-primary"
            :class="{ 'is-loading': isCreating }"
            :disabled="!canCreate"
            @click="confirm"
          >
            创建项目
          </button>
        </div>

        <p class="has-text-danger" v-if="error">{{ error }}</p>
      </div>
    </div>
    <button
      class="modal-close is-large"
      aria-label="close"
      @click="$emit('cancel')"
    ></button>
  </div>
</template>

<script>
import Spinner from '@/components/widgets/Spinner.vue'
import templatesApi from '@/store/api/templates'

export default {
  name: 'create-from-template-modal',

  components: { Spinner },

  props: {
    active: { type: Boolean, default: false }
  },

  emits: ['cancel', 'confirm'],

  data() {
    return {
      templates: [],
      selectedTemplateId: '',
      projectName: '',
      isLoadingTemplates: false,
      isCreating: false,
      error: ''
    }
  },

  computed: {
    selectedTemplate() {
      return this.templates.find((t) => t.id === this.selectedTemplateId)
    },

    canCreate() {
      return this.selectedTemplateId && this.projectName.trim().length > 0
    }
  },

  watch: {
    active(val) {
      if (val) {
        this.loadTemplates()
        this.selectedTemplateId = ''
        this.projectName = ''
        this.error = ''
      }
    }
  },

  methods: {
    async loadTemplates() {
      this.isLoadingTemplates = true
      try {
        this.templates = await templatesApi.getTemplates()
      } catch (err) {
        console.error('Failed to load templates:', err)
        this.templates = []
      }
      this.isLoadingTemplates = false
    },

    async confirm() {
      if (!this.canCreate) return
      this.isCreating = true
      this.error = ''
      try {
        const project = await templatesApi.createProjectFromTemplate(
          this.selectedTemplateId,
          { name: this.projectName.trim() }
        )
        this.$emit('confirm', project)
      } catch (err) {
        console.error('Failed to create project from template:', err)
        this.error = err?.body?.error || '创建失败，请重试'
      }
      this.isCreating = false
    }
  }
}
</script>

<style lang="scss" scoped>
.box {
  padding: 2em;
}

.subtitle {
  margin-bottom: 1.5em;
}

.template-info {
  background: var(--background-alt, #f8f8f8);
  border: 1px solid var(--border, #eee);
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 1em;
}

.template-desc {
  margin-bottom: 8px;
  color: var(--text-alt, #666);
}

.template-meta {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 1.5em;
}

.empty-state {
  text-align: center;
  padding: 30px;
  color: var(--text-alt, #999);
}
</style>
