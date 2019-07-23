import Vue from 'vue'
import Router from 'vue-router'
import HelloWorld from '@/components/HelloWorld'
import TicketList from '@/components/TicketList'
import Login from '@/components/Login'

Vue.use(Router)

let router = new Router({
  routes: [
    {
      path: '/',
      redirect: '/forms/apply_server'
    },
    {
      path: '/ticket',
      name: 'TicketList',
      component: TicketList
    },
    {
      path: '/forms/:name',
      name: 'FormView',
      component: HelloWorld
    },
    {
      path: '/login',
      name: 'Login',
      component: Login
    }
  ]
})
export default router
