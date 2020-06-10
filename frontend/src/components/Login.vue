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
      const strWindowFeatures = 'toolbar=no, menubar=no, width=800, height=600, top=100, left=100'
      const popup = window.open('/auth/oauth/keycloak', 'oauth', strWindowFeatures)
      if (!popup) return 'POPUP_FAILED'
      popup.focus()
      const app = this
      var timer = setInterval(function () {
        if (popup.closed) {
          clearInterval(timer)
          let next = app.$route.query.next
          if (next) {
            app.$router.push(next)
          } else {
            app.$router.push({name: 'Home'})
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
