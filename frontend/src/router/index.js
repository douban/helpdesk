import Vue from 'vue'
import Router from 'vue-router'
import HelloWorld from '@/components/HelloWorld'
import TicketList from '../components/TicketList'
import Login from '@/components/Login'

Vue.use(Router)

let router = new Router({
  routes: [
    {
      path: '/',
      name: 'Home',
      component: HelloWorld
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
router.beforeEach(
  (to, from, next) => {
    console.log(to)
    if (to.path === '/login') {
      next()
    } else {
      const axios = require('axios')
      axios.get('/api/auth/heartbeat').then(
        (response) => {
          if (response.data.data.status_code === 200) {
            next()
          } else {
            next('/login')
          }
        }
      ).catch(
        (error) => {
          console.log(error)
        }
      )
    }
  }
)
export default router
