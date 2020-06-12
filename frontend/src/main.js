// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue'
import App from './App'
import router from './router'
import store from './store'
import './assets/vue-select.min.css'
import './plugins/ant-design-vue.js'

Vue.config.productionTip = false

/* eslint-disable no-new */
let vm = new Vue({
  router,
  store,
  render: h => h(App)
})
vm.$mount('#app')
export {vm}
