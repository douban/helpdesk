<template>
  <a-layout>
    <a-layout-sider class="whiteBackground">
      <a-layout class="whiteBackground">
        <keep-alive>
          <h-sider></h-sider>
        </keep-alive>
      </a-layout>
    </a-layout-sider>
    <a-layout-content>
      <!--TODO an additional welcome sign could be added-->
      <a-skeleton />
    </a-layout-content>
  </a-layout>
</template>

<script>
export default {

  computed: {
    firstAction () {
      return this.$store.getters.firstAction
    }
  },
  watch: {
    firstAction (value) {
      if (value) {
        this.$router.push({name: 'action', params: {action: value.target_object}})
      }
    }
  }
}
</script>

<style scoped>

</style>
