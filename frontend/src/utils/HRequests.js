import {vm} from '../main.js'
import Vue from "vue";
const axios = require('axios')
const HRequest = axios.create({
  withCredentials: true
})

// let message = vm.$message

export function tokenInterceptor (instance) {
  instance.interceptors.request.use(config => {
    config.headers.Authorization = `Bearer ${Vue.prototype.$keycloak.token}`
    return config
  }, error => {
    return Promise.reject(error)
  })
}

HRequest.interceptors.response.use((response) => {
  // Do something with response data
  return response
}, function (error) {
  // Do something with response error
  if (error.response.status === 401) {
    // 401, unauthorized , redirect to login page
    vm.$message.warning('Login required, redirecting to login page...')
    if (vm.$route.name !== 'Login') {
      vm.$keycloak.loginFn()
    }
  } else if (error.response.status === 403) {
    // 403, insufficient privillege, Redirect to login page
    vm.$message.warning('Insufficient privilege!' + error.response.status + ':' + JSON.stringify(error.response.data))
    if (vm.$route.name !== 'Login') {
      vm.$keycloak.loginFn()
    }
  } else if (error.response.status >= 500) {
    vm.$message.error('Internal error, please contact webadmin' + error.response.status + ':' + JSON.stringify(error.response.data))
  } else {
    // > 500 internal error, notify only
    // > 404 notify only
    const rawMsg = JSON.stringify(error.response.data)
    const msg = rawMsg.length > 150 ? rawMsg.slice(0, 150) + '...' : rawMsg
    vm.$message.warning('Request failed: ' + error.response.status + ':' + msg)
  }
  return Promise.reject(error)
})

export {HRequest}
