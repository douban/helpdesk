import Vue from 'vue'
import Router from 'vue-router'
import HActionView from '@/components/HActionView'
import HTicketList from '@/components/HTicketList'
import Login from '@/components/Login'
import HHome from '../components/HHome'

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
      // TODO create another component for ticket detail
      component: HTicketList
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
