<template>
  <h-base>
    <a-layout class="padding24px">
      <a-layout-sider  width="300" class="whiteBackground">
          <a-layout class="whiteBackground">
            <h-sider></h-sider>
          </a-layout>
      </a-layout-sider>
      <a-layout-content>
        <h-form></h-form>
      </a-layout-content>
    </a-layout>
  </h-base>
</template>

<script>
import HSider from './HSider'
import HForm from './HForm'
import HBase from './HBase'
import ALayoutSider from 'ant-design-vue/es/layout/Sider'
export default {
  name: 'HActionView',
  components: {
    ALayoutSider,
    'h-sider': HSider,
    HForm,
    'h-base': HBase
  },
  data () {
    return {
      msg: 'Welcome to Your Vue.js App'
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
  .padding24px {
    padding: 0px 24px 24px;
  }
  .whiteBackground {
    background: #fff
  }
</style>
