<template>
  <a-layout :style="{ minHeight: '100vh' }">
    <h-header></h-header>
    <slot>Loading...</slot>
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

</style>
