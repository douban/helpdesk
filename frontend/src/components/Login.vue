<template>
  <a-layout :style="{ minHeight: '100vh' }">
    <a-layout-content>
      <a-row type="flex" justify="center" align="middle" :style="{ minHeight: '80vh' }">
        <a-button-group>
          <a-button
            @click="onLogin"
            type="primary"
            v-for="(provider, index) in openidProviders"
            v-bind:key="index"
            v-bind:name="provider"
          >
            Signin with {{ provider }}
          </a-button>
        </a-button-group>
      </a-row>
    </a-layout-content>
    <h-footer></h-footer>
  </a-layout>
</template>

<script>
import HFooter from './HFooter'
import {HRequest} from '../utils/HRequests'
export default {
  name: 'Login',
  components: {HFooter},
  mounted () {
    this.getProviders()
  },
  data () {
    return {
      openidProviders: []
    }
  },
  methods: {
    getProviders () {
      HRequest.get('/api/auth/providers').then(
        (response) => {
          this.openidProviders = response.data.data
        }
      ).catch()
    },
    onLogin () {
      console.log()
      let provider = event.target.name
      let strWindowFeatures = 'toolbar=no, menubar=no, width=800, height=600, top=100, left=100'
      const popup = window.open(`/auth/oauth/${provider}`, 'oauth', strWindowFeatures)
      if (!popup) return 'POPUP_FAILED'
      popup.focus()
      var timer = setInterval(() => {
        if (popup.closed) {
          clearInterval(timer)
          let next = this.$route.query.next
          if (next) {
            this.$router.push(next)
          } else {
            this.$router.push({name: 'Home'})
          }
        }
      }, 500)
    },
    purgeUserProfile () {
      this.$store.dispatch('deleteUserProfile')
    }
  }
}
</script>

<style scoped>

</style>
