<template>
  <a-layout :style="{ minHeight: '100vh' }">
    <notify-card />
    <h-header></h-header>
    <!-- the nuxt-child-key value does not matter here, it's just a key to prevent nuxt from rendering component again
      https://nuxtjs.org/docs/features/nuxt-components#the-nuxt-component
    -->
    <Nuxt class="padding24px" nuxt-child-key="doNotReMount" />
    <h-footer></h-footer>
  </a-layout>
</template>


<style scoped>
.padding24px {
  padding: 0px 24px 24px;
}
</style>
