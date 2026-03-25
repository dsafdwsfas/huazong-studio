<template>
  <div class="columns fixed-page">
    <div class="column main-column">
      <div class="storyboard page">
        <div class="page-header">
          <div class="flexrow">
            <span class="flexrow-item page-title">
              {{ $t('storyboard.title') || '分镜面板' }}
            </span>
            <div class="filler"></div>
          </div>
        </div>
        <storyboard-panel
          v-if="currentProduction"
          :production-id="currentProduction.id"
          :episode-id="currentEpisode?.id"
        />
        <div v-else class="has-text-centered mt-4">
          <p>{{ $t('storyboard.select_production') || '请先选择一个项目' }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import StoryboardPanel from '@/components/pages/storyboard/StoryboardPanel.vue'

export default {
  name: 'storyboard-page',

  components: {
    StoryboardPanel
  },

  computed: {
    ...mapGetters(['currentProduction', 'currentEpisode'])
  }
}
</script>

<style lang="scss" scoped>
.storyboard {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.page-header {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;

  .page-title {
    font-size: 1.1rem;
    font-weight: 600;
    margin: 0;
  }
}
</style>
