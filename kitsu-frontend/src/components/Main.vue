<template>
  <XyzTransition appear xyz="fade">
    <div class="main">
      <topbar />
      <sidebar />
      <router-view />
    </div>
  </XyzTransition>
</template>

<script>
import Topbar from '@/components/tops/Topbar.vue'
import Sidebar from '@/components/sides/Sidebar.vue'
import { initSocketManager, destroySocketManager } from '@/lib/socket-manager'

export default {
  name: 'main-wrapper',

  components: {
    Topbar,
    Sidebar
  },

  mounted() {
    this.$socket.connect()
    initSocketManager(this.$socket)
  },

  beforeUnmount() {
    destroySocketManager()
  }
}
</script>

<style>
.main {
  height: 100%;
  display: flex;
  flex-direction: column;
}
</style>
