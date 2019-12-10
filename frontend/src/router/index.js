import Vue from 'vue'
import Router from 'vue-router'
import HActionView from '@/components/HActionView'
import HTicketList from '@/components/HTicketList'
import Login from '@/components/Login'
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
      path: '/:name',
      name: 'FormView',
      component: HActionView
    },
    {
      path: '/login',
      name: 'Login',
      component: Login
    }
  ]
})
export default router
