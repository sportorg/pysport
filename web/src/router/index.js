import Vue from 'vue'
import Router from 'vue-router'
import RaceInfo from '../components/race-info/RaceInfo.vue'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/',
      name: 'RaceInfo',
      component: RaceInfo
    }
  ]
})
