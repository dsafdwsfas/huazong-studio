<template>
  <div class="navbar">
    <aside :class="{ 'hidden-bar': isSidebarHidden, smallfont: isLongLocale }">
      <div>
        <router-link class="home-link" to="/" @click="toggleSidebar()">
          <div class="company-logo has-text-centered" :title="title">
            <img
              :src="logoPath"
              v-if="organisation && organisation.has_avatar"
            />
            <img
              src="../../assets/kitsu-text-dark.svg"
              width="180"
              v-else-if="isDarkTheme"
            />
            <img src="../../assets/kitsu-text.svg" width="180" v-else />
          </div>
        </router-link>

        <section>
          <div v-if="!isCurrentUserClient">
            <h2>{{ $t('main.workspace') }}</h2>

            <p @click="toggleSidebar()">
              <router-link :to="{ name: 'todos' }">
                <kitsu-icon class="nav-icon" name="my-tasks" />
                {{ $t('tasks.my_tasks') }}
              </router-link>
            </p>
            <p
              @click="toggleSidebar()"
              v-if="isCurrentUserSupervisor || isCurrentUserManager"
            >
              <router-link :to="{ name: 'checks' }">
                <kitsu-icon class="nav-icon" name="my-checks" />
                {{ $t('tasks.my_checks') }}
              </router-link>
            </p>
            <p @click="toggleSidebar()">
              <router-link :to="{ name: 'entity-chats' }">
                <kitsu-icon class="nav-icon" name="message" />
                {{ $t('chats.title') }}
              </router-link>
            </p>
            <p @click="toggleSidebar()">
              <router-link :to="{ name: 'open-productions' }">
                <kitsu-icon class="nav-icon" name="my-productions" />
                {{ $t('productions.open_productions') }}
              </router-link>
            </p>
          </div>

          <div v-if="!isCurrentUserClient && !isCurrentUserVendor">
            <h2>{{ $t('main.studio') }}</h2>

            <p @click="toggleSidebar()" v-if="isCurrentUserAdmin">
              <router-link :to="{ name: 'productions' }">
                <kitsu-icon class="nav-icon" name="productions" />
                {{ $t('productions.title') }}
              </router-link>
            </p>

            <p @click="toggleSidebar()" v-if="isCurrentUserAdmin">
              <router-link :to="{ name: 'people' }">
                <kitsu-icon class="nav-icon" name="team" />
                {{ $t('people.title') }}
              </router-link>
            </p>

            <p @click="toggleSidebar()">
              <router-link :to="{ name: 'timesheets' }">
                <kitsu-icon class="nav-icon" name="timesheets" />
                {{ $t('timesheets.title') }}
              </router-link>
            </p>

            <p @click="toggleSidebar()" v-if="isCurrentUserAdmin">
              <router-link :to="{ name: 'main-schedule' }">
                <kitsu-icon class="nav-icon" name="schedule" />
                {{ $t('schedule.title_main') }}
              </router-link>
            </p>

            <p
              @click="toggleSidebar()"
              v-if="isCurrentUserSupervisor || isCurrentUserManager"
            >
              <router-link
                style="position: relative"
                :to="{ name: 'team-schedule' }"
              >
                <kitsu-icon class="nav-icon" name="team-schedule" />
                {{ $t('team_schedule.title_main') }}
              </router-link>
            </p>
            <p
              @click="toggleSidebar()"
              v-if="isCurrentUserSupervisor || isCurrentUserManager"
            >
              <router-link :to="{ name: 'all-tasks' }">
                <kitsu-icon class="nav-icon" name="check" />
                {{ $t('tasks.all_tasks') }}
              </router-link>
            </p>
            <p @click="toggleSidebar()">
              <router-link
                :to="{ name: 'newsfeed' }"
                v-if="isCurrentUserManager"
              >
                <kitsu-icon class="nav-icon" name="newsFeed" />
                {{ $t('news.title') }}
              </router-link>
            </p>
            <p @click="toggleSidebar()" v-if="mainConfig.indexer_configured">
              <router-link :to="{ name: 'entity-search' }">
                <kitsu-icon class="nav-icon" name="search" />
                {{ $t('search.title') }}
              </router-link>
            </p>
            <p @click="toggleSidebar()">
              <router-link :to="{ name: 'asset-library' }">
                <kitsu-icon class="nav-icon" name="assets" />
                {{ $t('library.asset_library') }}
              </router-link>
            </p>
            <p @click="toggleSidebar()">
              <router-link :to="{ name: 'global-asset-library' }">
                <kitsu-icon class="nav-icon" name="assets" />
                全局资产库
              </router-link>
            </p>
            <p @click="toggleSidebar()">
              <router-link :to="{ name: 'asset-node-graph' }">
                <kitsu-icon class="nav-icon" name="assets" />
                资产图谱
              </router-link>
            </p>
            <p @click="toggleSidebar()">
              <router-link :to="{ name: 'asset-dashboard' }">
                <bar-chart3-icon class="nav-icon" />
                统计看板
              </router-link>
            </p>
            <p
              @click="toggleSidebar()"
              v-if="isCurrentUserAdmin || isCurrentUserManager"
            >
              <router-link :to="{ name: 'asset-category-manager' }">
                <rows4-icon class="nav-icon" />
                分类管理
              </router-link>
            </p>
            <p
              @click="toggleSidebar()"
              v-if="isCurrentUserAdmin || isCurrentUserManager"
            >
              <router-link
                :to="{ name: 'asset-review-queue' }"
                style="position: relative"
              >
                <clipboard-check-icon class="nav-icon" />
                审核队列
                <span
                  class="review-badge-count"
                  v-if="reviewPendingCount > 0"
                >
                  {{ reviewPendingCount }}
                </span>
              </router-link>
            </p>
          </div>
          <div v-if="isCurrentUserAdmin">
            <h2>开发者</h2>
            <p @click="toggleSidebar()">
              <router-link :to="{ name: 'api-key-manager' }">
                <key-round-icon class="nav-icon" />
                API 密钥
              </router-link>
            </p>
            <p @click="toggleSidebar()">
              <router-link :to="{ name: 'api-documentation' }">
                <book-open-icon class="nav-icon" />
                API 文档
              </router-link>
            </p>
          </div>

          <div v-for="plugin in studioPlugins" :key="plugin.id">
            <p @click="toggleSidebar()">
              <router-link
                :to="{
                  name: 'plugin',
                  params: { plugin_id: plugin.plugin_id }
                }"
              >
                <icon :name="plugin.icon" />
                {{ plugin.name }}
              </router-link>
            </p>
          </div>

          <div v-if="isCurrentUserAdmin">
            <h2>{{ $t('main.admin') }}</h2>
            <p @click="toggleSidebar()">
              <router-link :to="{ name: 'departments' }">
                <kitsu-icon class="nav-icon" name="departments" />
                {{ $t('departments.title') }}
              </router-link>
            </p>
            <p @click="toggleSidebar()">
              <router-link :to="{ name: 'studios' }">
                <building-icon class="nav-icon" />
                {{ $t('studios.title') }}
              </router-link>
            </p>
            <p @click="toggleSidebar()">
              <router-link :to="{ name: 'task-types' }">
                <kitsu-icon class="nav-icon" name="task-types" />
                {{ $t('task_types.title') }}
              </router-link>
            </p>
            <p @click="toggleSidebar()">
              <router-link
                :to="{ name: 'task-status' }"
                class="task-status-link"
              >
                <kitsu-icon class="nav-icon" name="task-status" />
                {{ $t('task_status.title') }}
              </router-link>
            </p>
            <p @click="toggleSidebar()">
              <router-link :to="{ name: 'asset-types' }">
                <kitsu-icon class="nav-icon" name="asset-types" />
                {{ $t('asset_types.title') }}
              </router-link>
            </p>
            <!-- 画宗: Budget/SalaryScale/Hardware 已隐藏 (1.6) -->
            <p @click="toggleSidebar()">
              <router-link :to="{ name: 'software-licenses' }">
                <egg-icon class="nav-icon" />
                {{ $t('software_licenses.title') }}
              </router-link>
            </p>
            <p @click="toggleSidebar()">
              <router-link :to="{ name: 'custom-actions' }">
                <kitsu-icon class="nav-icon" name="custom" />
                {{ $t('custom_actions.title') }}
              </router-link>
            </p>
            <p @click="toggleSidebar()">
              <router-link :to="{ name: 'status-automations' }">
                <kitsu-icon class="nav-icon" name="automations" />
                {{ $t('status_automations.title') }}
              </router-link>
            </p>
            <p @click="toggleSidebar()">
              <router-link :to="{ name: 'backgrounds' }">
                <globe-icon class="nav-icon" />
                {{ $t('backgrounds.title') }}
              </router-link>
            </p>
            <p @click="toggleSidebar()">
              <router-link :to="{ name: 'bots' }">
                <bot-icon class="nav-icon" />
                {{ $t('bots.title') }}
              </router-link>
            </p>
            <p @click="toggleSidebar()">
              <router-link :to="{ name: 'settings' }">
                <kitsu-icon class="nav-icon" name="settings" />
                {{ $t('settings.title') }}
              </router-link>
            </p>
            <p @click="toggleSidebar()">
              <router-link :to="{ name: 'logs' }">
                <kitsu-icon class="nav-icon" name="logs" />
                {{ $t('logs.title') }}
              </router-link>
            </p>
          </div>
        </section>
      </div>
    </aside>
    <div
      id="c-mask"
      @click="toggleSidebar()"
      :class="{ 'is-active': !isSidebarHidden }"
    ></div>
  </div>
</template>

<script>
import {
  BarChart3Icon,
  BookOpenIcon,
  BotIcon,
  BuildingIcon,
  ClipboardCheckIcon,
  ComputerIcon,
  EggIcon,
  GlobeIcon,
  KeyRoundIcon,
  Rows4Icon
} from 'lucide-vue-next'
import { defineAsyncComponent } from 'vue'
import { mapGetters, mapActions } from 'vuex'

const Icon = defineAsyncComponent(() => import('@/components/widgets/Icon.vue'))

import KitsuIcon from '@/components/widgets/KitsuIcon.vue'

export default {
  name: 'sidebar',

  components: {
    BarChart3Icon,
    BookOpenIcon,
    BotIcon,
    BuildingIcon,
    ClipboardCheckIcon,
    ComputerIcon,
    EggIcon,
    GlobeIcon,
    Icon,
    KeyRoundIcon,
    KitsuIcon,
    Rows4Icon
  },

  data() {
    return {
      title: '',
      logoPath: ''
    }
  },

  mounted() {
    this.reset()
    if (this.isCurrentUserAdmin || this.isCurrentUserManager) {
      this.loadReviewStats()
    }
  },

  computed: {
    ...mapGetters([
      'isDarkTheme',
      'isCurrentUserAdmin',
      'isCurrentUserClient',
      'isCurrentUserManager',
      'isCurrentUserSupervisor',
      'isCurrentUserVendor',
      'isSidebarHidden',
      'mainConfig',
      'organisation',
      'reviewPendingCount',
      'studioPlugins'
    ]),

    isLongLocale() {
      return this.$i18n.locale === 'ja' || this.$i18n.locale === 'fr'
    }
  },

  methods: {
    ...mapActions(['toggleSidebar', 'loadReviewStats']),

    reset() {
      this.title = this.organisation.name
      this.logoPath =
        `/api/pictures/thumbnails/organisations/` +
        `${this.organisation.id}.png?t=${new Date().toISOString()}`
    }
  },

  watch: {
    organisation() {
      this.reset()
    }
  }
}
</script>

<style lang="scss" scoped>
.dark aside {
  background-color: #2f3136;
  color: $white-grey;

  a {
    color: $white-grey;
  }
}

aside {
  position: fixed;
  top: 0;
  bottom: 0;
  left: 0;
  width: 230px;
  background-color: white;
  padding: 15px;
  overflow-y: auto;
  z-index: 205;
  box-shadow: 1px 0 6px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;

  h2 {
    border: 0;
    text-transform: uppercase;
    font-size: 1em;
    color: $grey;
  }
}

aside.hidden-bar {
  left: -250px;
  transition: all 0.3s ease;
}

aside p a {
  font-size: 1.4em;
  color: $grey-strong;
  display: flex;
  align-items: center;
  font-weight: 300;

  svg {
    margin-right: 0.5em;
  }
}

aside section {
  margin-bottom: 2em;
}

.sidebar-title {
  margin-top: 0.5em;
  margin-bottom: 1.5em;
  text-align: center;
  font-size: 1.6em;
}

.company-logo {
  width: 200px;
  img {
    border-radius: 5px;
  }
}

#c-mask {
  position: fixed;
  z-index: 204;
  top: 0;
  left: 0;
  overflow: hidden;
  width: 0;
  height: 0;
  background-color: #000;
  opacity: 0;
}

#c-mask.is-active {
  width: 100%;
  height: 100%;
}

h2 {
  margin-top: 2em;
  margin-bottom: 0.3em;
}

p {
  padding-left: 0.3em;
}

p:hover {
  cursor: pointer;
  background: var(--background-hover);
  border-radius: 5px;
  transform: scale(1.05);
  transition: 0.2s ease transform;
}

.nav-icon {
  margin-left: 0;
  margin-right: 0.5em;
  width: 20px;
}

.review-badge-count {
  position: absolute;
  right: -4px;
  top: -2px;
  background: #e74c3c;
  color: #fff;
  font-size: 0.6em;
  font-weight: 700;
  min-width: 18px;
  height: 18px;
  line-height: 18px;
  text-align: center;
  border-radius: 9px;
  padding: 0 4px;
}

.smallfont p {
  font-size: 0.85em;
}

@media screen and (max-width: 768px) {
  .company-logo img {
    width: 40px;
    margin: 0;
    flex: 1;
  }

  .home-link {
    display: flex;
    flex-direction: row;
    align-items: center;
  }

  .home-link h2 {
    margin-bottom: 0;
  }
}
</style>
