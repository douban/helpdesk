<template>
  <h-base>
    <a-layout class="padding24px">
      <a-layout-sider  width="300" class="whiteBackground">
        <a-layout class="whiteBackground">
          <h-sider></h-sider>
        </a-layout>
      </a-layout-sider>
      <a-layout-content>
        <!--TODO an additional welcome sign could be added-->
        <a-skeleton />
      </a-layout-content>
    </a-layout>
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
    setInterval(() => {
      // in case of slow network , try to redirect repeatedly
      if (this.$store.getters.firstAction) {
        this.$router.push({name: 'FormView', params: {name: this.$store.getters.firstAction.target_object}})
      }
    }, 1000)
  }
}
</script>

<style scoped>
  .padding24px {
    padding: 0px 24px 24px;
  }
  .whiteBackground {
    background: #fff
  }
</style>
