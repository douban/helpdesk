<template>
  <a-layout-header>

    <a-menu
      theme="dark"
      mode="horizontal"
      :style="{ lineHeight: '64px' }"
      :selected-keys = "selectedMenu"
    >
      <a-menu-item key="1">
        <NuxtLink to="/">Helpdesk</NuxtLink>
      </a-menu-item>
      <a-menu-item key="2">
        <NuxtLink :to="{name: 'ticket'}">Tickets</NuxtLink>
      </a-menu-item>
       <a-menu-item key="3">
        <NuxtLink :to="{name: 'policies'}">Approval Flow</NuxtLink>
      </a-menu-item>
      <a-sub-menu :style="{ float: 'right' }">
        <span slot="title">
            <span :style="{margin: '10px'}">{{ user.name }}</span>
            <a-avatar shape="square" icon="user"
                      :src="user.avatar"
            />
        </span>
        <a-menu-item key="3">
          <a href="/api/user/me">
          <!-- TODO a user profile page is needed -->
            <i class="glyphicon glyphicon-user"></i>
            whoami
          </a>
        </a-menu-item>
        <a-menu-item key="4" @click="logout">
          logout
        </a-menu-item>
      </a-sub-menu>
    </a-menu>

  </a-layout-header>
</template>

<script>
export default {
  name: 'HHeader',
  computed: {
    user () {
      return this.$store.state.userProfile
    },
    selectedMenu () {
      const ticketRouteNames = ['ticket', 'ticket-id']
      if (ticketRouteNames.includes(this.$route.name)) {
        return ['2']
      } else return ['1']
    }
  },
  mounted () {
    this.updateUserProfile()
  },
  methods: {
    updateUserProfile () {
      if (!this.$store.getters.isAuthenticated) {
        this.$axios.get('/api/user/me').then(
          (response) => {
            this.$store.dispatch('updateUserProfile', response.data)
          }
        )
      }
    },
    logout () {
      this.$axios.post('/auth/logout').then(() => {
        document.cookie = 'session' + '=; expires=Thu, 01 Jan 1970 00:00:01 GMT;'
        this.$router.push({name: 'login'})
      })
    }
  }
}
</script>

<style scoped>

</style>
