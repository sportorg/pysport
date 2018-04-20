// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue'
import VueResource from 'vue-resource'
import BootstrapVue from 'bootstrap-vue'
import VueScrollTo from 'vue-scrollto'
import App from './App'
import router from './router'
import store from './store'
import resize from './directives/resize'
import hhmmss from './filters/hhmmss'

Vue.use(VueResource)
Vue.use(BootstrapVue)
Vue.use(VueScrollTo)
Vue.directive('resize', resize)
Vue.filter('hhmmss', hhmmss)

Vue.http.options.root = 'api/v1'

Vue.config.productionTip = false

router.beforeEach((to, from, next) => {
  store.commit('setLoading', true)
  next()
})

router.afterEach((to, from) => {
  store.commit('setLoading', false)
})

window.shutDown = () => {
  console.log('Server shutting down...')
  Vue.http.post('shutdown').then()
}

/* eslint-disable no-new */
new Vue({
  el: '#app',
  router,
  store,
  components: { App },
  template: '<App/>'
})
