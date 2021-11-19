<template>
  <a-layout :style="{ minHeight: '100vh' }">
    <a-layout-content>
      <a-row type="flex" justify="center" align="middle" :style="{ minHeight: '80vh' }">
        <a-button-group>
          <a-button
            v-for="(provider, index) in openidProviders"
            :key="index"
            type="primary"
            :name="provider"
            @click="onLogin"
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
export default {
  name: 'Login',
  layout: 'blank',
  data () {
    return {
      openidProviders: []
    }
  },
  mounted () {
    this.getProviders()
  },
  methods: {
    getProviders () {
      this.$axios.get('/api/auth/providers').then(
        (response) => {
          this.openidProviders = response.data
        }
      ).catch()
    },
    onLogin () {
      const provider = event.target.name
      const strWindowFeatures = 'toolbar=no, menubar=no, width=800, height=600, top=100, left=100'
      const popup = window.open(`/auth/oauth/${provider}`, 'oauth', strWindowFeatures)
      if (!popup) return 'POPUP_FAILED'
      popup.focus()
      const timer = setInterval(() => {
        if (popup.closed) {
          clearInterval(timer)
          const next = this.$route.query.next
          if (next) {
            this.$router.push(next)
          } else {
            this.$router.push({ name: 'index' })
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
