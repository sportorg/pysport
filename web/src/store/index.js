import Vue from 'vue'
import Vuex from 'vuex'
import app from './modules/app'
import race from './modules/race'

Vue.use(Vuex)

const debug = process.env.NODE_ENV !== 'production'

export default new Vuex.Store({
  modules: {
    app,
    race
  },
  strict: debug
})
