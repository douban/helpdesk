<template>
  <h-base>
    <a-layout class="padding24px">
      <a-row>
        <a-col :span="6">
          <a-layout class="whiteBackground" width="300">
            <h-sider></h-sider>
          </a-layout>
        </a-col>
        <a-col :span="18" >
          <h-form></h-form>
        </a-col>
      </a-row>
      <h-drawer v-if="this.$store.getters.isAdmin"></h-drawer>
    </a-layout>
  </h-base>
</template>

<script>
import HSider from './HSider'
import HForm from './HForm'
import HDrawer from './HDrawer'
import HBase from './HBase'
export default {
  name: 'HelloWorld',
  components: {
    HDrawer,
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
