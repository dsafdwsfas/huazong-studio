<template>
  <div class="productions page fixed-page">
    <div class="flexrow page-header">
      <page-title class="filler" :text="$t('productions.title')" />
      <button-simple
        class="flexrow-item"
        :text="$t('productions.load_stats')"
        :is-loading="loading.stats"
        @click="reloadStats"
      />
      <button-simple
        class="flexrow-item"
        text="从模板创建"
        icon="copy"
        @click="modals.isTemplateDisplayed = true"
      />
      <button-link
        class="flexrow-item"
        :text="$t('productions.new_production')"
        icon="plus"
        :path="{ name: 'new-production' }"
      />
    </div>

    <production-list
      :entries="productions"
      :production-stats="productionStats"
      :is-loading="isProductionsLoading"
      :is-error="isProductionsLoadingError"
      @delete-clicked="onDeleteClicked"
      @edit-clicked="onEditClicked"
      @save-template="onSaveTemplate"
    />

    <edit-production-modal
      active
      :is-loading="loading.edit"
      :is-error="errors.edit"
      :production-to-edit="productionToEdit"
      @cancel="modals.isEditDisplayed = false"
      @fileselected="onProductionPictureSelected"
      @confirm="confirmEditProduction"
      v-if="modals.isEditDisplayed"
    />

    <create-from-template-modal
      :active="modals.isTemplateDisplayed"
      @cancel="modals.isTemplateDisplayed = false"
      @confirm="onProjectCreatedFromTemplate"
    />

    <hard-delete-modal
      :active="modals.isDeleteDisplayed"
      :is-loading="loading.del"
      :is-error="errors.del"
      :text="deleteText()"
      :error-text="$t('productions.delete_error')"
      :lock-text="currentLockText"
      @cancel="modals.isDeleteDisplayed = false"
      @confirm="confirmDeleteProduction"
    />
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'

import templatesApi from '@/store/api/templates'
import ButtonLink from '@/components/widgets/ButtonLink.vue'
import ButtonSimple from '@/components/widgets/ButtonSimple.vue'
import CreateFromTemplateModal from '@/components/modals/CreateFromTemplateModal.vue'
import EditProductionModal from '@/components/modals/EditProductionModal.vue'
import HardDeleteModal from '@/components/modals/HardDeleteModal.vue'
import ProductionList from '@/components/lists/ProductionList.vue'
import PageTitle from '@/components/widgets/PageTitle.vue'

export default {
  name: 'productions',

  components: {
    ButtonLink,
    ButtonSimple,
    CreateFromTemplateModal,
    HardDeleteModal,
    EditProductionModal,
    PageTitle,
    ProductionList
  },

  data() {
    return {
      errors: {
        del: false,
        edit: false
      },
      loading: {
        del: false,
        edit: false,
        stats: false
      },
      modals: {
        isEditDisplayed: false,
        isDeleteDisplayed: false,
        isTemplateDisplayed: false
      },
      productionStats: {},
      productionToDelete: null,
      productionToEdit: null
    }
  },

  computed: {
    ...mapGetters([
      'isProductionsLoading',
      'isProductionsLoadingError',
      'productionAvatarFormData',
      'productions'
    ]),

    currentLockText() {
      return this.productionToDelete?.name || ''
    }
  },

  async created() {
    await this.loadProductions()
  },

  methods: {
    ...mapActions([
      'deleteProduction',
      'editProduction',
      'loadProductions',
      'loadProductionStats',
      'storeProductionPicture',
      'uploadProductionAvatar'
    ]),

    // Actions

    async confirmEditProduction(form) {
      this.loading.edit = true
      this.errors.edit = false
      try {
        if (this.productionAvatarFormData) {
          await this.uploadProductionAvatar(this.productionToEdit.id)
        }
        await this.editProduction({
          ...form,
          id: this.productionToEdit.id
        })
        this.modals.isEditDisplayed = false
      } catch (error) {
        console.error(error)
        this.errors.edit = true
      }
      this.loading.edit = false
    },

    confirmDeleteProduction() {
      this.loading.del = true
      this.errors.del = false
      this.deleteProduction(this.productionToDelete)
        .then(() => {
          this.modals.isDeleteDisplayed = false
          this.loading.del = false
        })
        .catch(err => {
          console.error(err)
          this.errors.del = true
          this.loading.del = false
        })
    },

    deleteText() {
      const production = this.productionToDelete
      if (production) {
        return this.$t('productions.delete_text', { name: production.name })
      } else {
        return ''
      }
    },

    // Events

    onEditClicked(production) {
      this.storeProductionPicture(null)
      this.productionToEdit = production
      this.modals.isEditDisplayed = true
    },

    onDeleteClicked(production) {
      this.productionToDelete = production
      this.modals.isDeleteDisplayed = true
    },

    onProductionPictureSelected(formData) {
      this.storeProductionPicture(formData)
    },

    async onSaveTemplate(production) {
      const name = prompt(`输入模板名称（基于"${production.name}"）:`)
      if (!name) return
      try {
        await templatesApi.createTemplate({
          name,
          from_project_id: production.id,
          description: `基于项目「${production.name}」创建`
        })
        alert('模板保存成功！')
      } catch (err) {
        console.error('Failed to save template:', err)
        alert('保存模板失败: ' + (err?.body?.error || '未知错误'))
      }
    },

    async onProjectCreatedFromTemplate() {
      this.modals.isTemplateDisplayed = false
      await this.loadProductions()
    },

    async reloadStats() {
      this.loading.stats = true
      this.productionStats = await this.loadProductionStats()
      this.loading.stats = false
    }
  },

  head() {
    return {
      title: `${this.$t('productions.title')} - 画宗`
    }
  }
}
</script>
