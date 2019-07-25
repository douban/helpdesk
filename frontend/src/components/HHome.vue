<template>
  <h-base>
    <a-layout-sider  width="300" class="whiteBackground">
      <a-layout class="whiteBackground">
        <h-sider></h-sider>
      </a-layout>
    </a-layout-sider>
    <a-layout-content>
      <!--TODO an additional welcome sign could be added-->
      <a-skeleton />
    </a-layout-content>
  </h-base>
</template>

<script>
import HSider from './HSider'
import HBase from './HBase'
import ALayoutSider from 'ant-design-vue/es/layout/Sider'
export default {
  name: 'HHome',
  components: {
    ALayoutSider,
    'h-sider': HSider,
    'h-base': HBase
  },
  mounted () {
    setTimeout(() => {
      // in case of slow network , delay for a while before redirect
      if (this.$store.getters.firstAction) {
        this.$router.push({name: 'FormView', params: {name: this.$store.getters.firstAction.target_object}})
      }
    }, 1000)
  }
}
</script>

<style scoped>

</style>
