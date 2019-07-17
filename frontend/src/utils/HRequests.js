import {vm} from '../main.js'
const axios = require('axios')
const HRequest = axios.create({
  withCredentials: true
})

// let message = vm.$message

HRequest.interceptors.response.use((response) => {
  // Do something with response data
  console.log('global!!!')
  return response
}, function (error) {
  // Do something with response error
  if (error.response.status === 401) {
    // 401, 未认证, 重定向至登录
    vm.$message.warning('用户未登录, 即将重定向至登录页...')
    vm.$router.push('/login')
  } else if (error.response.status === 403) {
    // 403, 权限不足, 提示联系管理员 TODO 后端未改造
    vm.$message.warning('账户权限不足, 请切换账号或联系管理员' + error.response.status + ':' + error.response.data)
    vm.$router.push('/login')
  } else if (error.response.status >= 500) {
    console.log(error.response.data)
    vm.$message.error('服务器内部错误, 请联系管理员' + error.response.status + ':' + error.response.data)
  } else {
    vm.$message.warning('请求失败: ' + error.response.status + ':' + error.response.data)
  }
  // > 500 内部错误, 提示联系管理员
  // > 404 只提示
  // 超时在这里吗?
  return Promise.reject(error)
})

export {HRequest}
