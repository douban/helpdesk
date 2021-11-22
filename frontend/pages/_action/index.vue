<template>
  <a-layout>
    <a-layout-sider  width="300" class="whiteBackground">
      <a-layout class="whiteBackground">
        <h-sider></h-sider>
      </a-layout>
    </a-layout-sider>
    <a-layout-content>
      <h-form></h-form>
    </a-layout-content>
  </a-layout>
</template>

<script>
export default {
  name: 'Index'
}
</script>

<style scoped>
.whiteBackground {
  background: #fff
}
</style>
