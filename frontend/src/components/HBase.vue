<template>
  <a-layout :style="{ minHeight: '100vh' }">
    <h-header></h-header>
    <a-layout class="padding24px">
      <slot>Loading...</slot>
    </a-layout>
    <h-footer></h-footer>
  </a-layout>
</template>

<script>
import HFooter from './HFooter'
import HHeader from './HHeader'
export default {
  // Base Component for all other components except for Login, following methods would be called:
  // 1. None
  name: 'HBase',
  components: {HHeader, HFooter}
}
</script>

<style scoped>
.padding24px {
  padding: 0px 24px 24px;
}
</style>
