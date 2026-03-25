import { createStore } from 'vuex'

import * as getters from '@/store/getters'

import assets from '@/store/modules/assets'
import assetTypes from '@/store/modules/assettypes'
import backgrounds from '@/store/modules/backgrounds'
import breakdown from '@/store/modules/breakdown'
import budget from '@/store/modules/budget'
import concepts from '@/store/modules/concepts'
import customActions from '@/store/modules/customactions'
import departments from '@/store/modules/departments'
import edits from '@/store/modules/edits'
import entities from '@/store/modules/entities'
import episodes from '@/store/modules/episodes'
import files from '@/store/modules/files'
import assetCategories from '@/store/modules/assetCategories'
import assetExport from '@/store/modules/assetExport'
import globalAssets from '@/store/modules/globalAssets'
import assetSearch from '@/store/modules/assetSearch'
import apiKeys from '@/store/modules/apiKeys'
import assetGraph from '@/store/modules/assetGraph'
import assetStats from '@/store/modules/assetStats'
import assetUsages from '@/store/modules/assetUsages'
import assetReviews from '@/store/modules/assetReviews'
import assetVersions from '@/store/modules/assetVersions'
import hardware from '@/store/modules/hardware'
import login from '@/store/modules/login'
import main from '@/store/modules/main'
import news from '@/store/modules/news'
import notifications from '@/store/modules/notifications'
import people from '@/store/modules/people'
import playlists from '@/store/modules/playlists'
import productions from '@/store/modules/productions'
import schedule from '@/store/modules/schedule'
import sequences from '@/store/modules/sequences'
import shots from '@/store/modules/shots'
import software from '@/store/modules/software'
import statusAutomations from '@/store/modules/statusautomation'
import storyboard from '@/store/modules/storyboard'
import studios from '@/store/modules/studios'
import taskStatus from '@/store/modules/taskstatus'
import taskTypes from '@/store/modules/tasktypes'
import tasks from '@/store/modules/tasks'
import presence from '@/store/modules/presence'
import uploads from '@/store/modules/uploads'
import user from '@/store/modules/user'

const modules = {
  apiKeys,
  assetCategories,
  assetExport,
  assetReviews,
  assets,
  assetTypes,
  backgrounds,
  breakdown,
  budget,
  concepts,
  customActions,
  departments,
  edits,
  entities,
  episodes,
  files,
  globalAssets,
  assetSearch,
  assetGraph,
  assetStats,
  assetUsages,
  assetVersions,
  hardware,
  login,
  main,
  people,
  playlists,
  productions,
  news,
  notifications,
  schedule,
  sequences,
  shots,
  software,
  statusAutomations,
  storyboard,
  studios,
  presence,
  tasks,
  taskTypes,
  taskStatus,
  uploads,
  user
}
export default createStore({
  getters,
  modules,
  strict: false
})
