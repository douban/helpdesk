<template>
  <span />
</template>

<script>
export default {
  name: 'NotifyCard',
  created () {
    this.$store.subscribe((mutation, state) => {
      if (mutation.type === 'alert/showMessage') {
        this.$message[mutation.payload.level](mutation.payload.content)
      }
    })
  }
}
</script>

<style scoped>

</style>
