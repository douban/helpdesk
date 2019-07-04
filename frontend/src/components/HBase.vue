<template>
  <a-layout :style="{ minHeight: '100vh' }">
    <h-header></h-header>
    <!-- 把实际内容的高度设置一个最低值, 保证 footer 可以在底部-->
    <slot>Under construction</slot>
    <h-footer></h-footer>
  </a-layout>
</template>

<script>
import HFooter from './HFooter'
import HHeader from './HHeader'
const axios = require('axios')
export default {
  // 这个组件是除了Login之外所有组件的base, 进入到这个组件的用户一定是登录用户, 这里会做一些操作包括如下:
  // 1. 用户信息的获取和缓存
  // 2. 暂无其他
  name: 'HBase',
  components: {HHeader, HFooter},
  methods: {
    getUserProfile () {
      // 1. state中有没有
      // 2. localstorage 中有没有
      // 3. 都找不到就请求api , 并且在state 和localstorage 中都加上
      if (!this.$state.isAuthenticated()) {
        axios.get('/api/user/me').then(
          (response) => {
            if (response.data.data.is_authenticated === true) {
              this.$store.dispatch('updateUserProfile', response.data.data)
            } else {
              // 理论上来说不可能到这一步, 但我还是加上else 判断吧
              this.$router.push('/login')
            }
          }
        )
      }
    }
  }
}
</script>

<style scoped>

</style>
