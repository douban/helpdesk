<template>
  <a-layout>
    <a-layout-sider v-model="collapsed" width="300px" class="whiteBackground" collapsible :trigger=null>
      <a-layout class="whiteBackground">
        <h-sider></h-sider>
        <a-icon
          class="trigger" style="margin-top: 20px; margin-bottom: 20px"
          :type="collapsed ? 'menu-unfold' : 'menu-fold'"
          @click="() => (collapsed = !collapsed)"
        />
      </a-layout>
    </a-layout-sider>
    <a-layout-content>
      <h-form></h-form>
    </a-layout-content>
  </a-layout>
</template>

<script>
export default {
  data() {
    return { collapsed: false };
  }
}
</script>

<style scoped>
.whiteBackground {
  background: #fff
}
</style>
