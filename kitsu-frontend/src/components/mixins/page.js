/*
 * This mixin is used to format the page title based on the current context.
 */
import { mapGetters } from 'vuex'

export const pageMixin = {
  computed: {
    ...mapGetters(['currentProduction, currentEpisode, isTVShow'])
  },

  methods: {},

  head() {
    if (this.currentProduction) {
      if (this.isTVSHow && this.currentEpisode) {
        return {
          title:
            `${this.currentProduction.name} - ` +
            `${this.currentEpisode.name} | {this.pageTitle} - 画宗`
        }
      } else {
        return {
          title: `${this.currentProduction.name} | ${this.pageTitle} - 画宗`
        }
      }
    } else {
      return {
        title: `${this.pageTitle} - 画宗`
      }
    }
  }
}
