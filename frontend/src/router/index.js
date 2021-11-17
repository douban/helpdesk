import Vue from 'vue'
import Router from 'vue-router'
import HActionView from '@/components/HActionView'
import HTicketList from '@/components/HTicketList'
import HHome from '../components/HHome'
import HTicketDetail from '../components/HTicketDetail'

Vue.use(Router)

let router = new Router({
  mode: 'history',
  routes: [
    {
      path: '/',
      name: 'Home',
      component: HHome
    },
    {
      path: '/ticket',
      name: 'HTicketList',
      component: HTicketList
    },
    {
      path: '/ticket/:id',
      name: 'HTicketDetail',
      component: HTicketDetail
    },
    {
      path: '/ticket/:id/:action',
      name: 'HTicketQuickPass',
      component: HTicketDetail
    },
    {
      // Make sure this route is the last, as it can match all route
      // See also: https://router.vuejs.org/guide/essentials/dynamic-matching.html#matching-priority
      path: '/:name',
      name: 'FormView',
      component: HActionView
    }
  ]
})
export default router
