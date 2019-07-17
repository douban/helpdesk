<template>
  <a-form-item
    :label="label"
  >
    <a-checkbox
      @change="onCheckBoxChange"
      :checked="value"
    >
    </a-checkbox>
  </a-form-item>
</template>

<script>
export default {
  name: 'CheckBoxInput',
  props: ['label', 'name', 'value'],
  methods: {
    onCheckBoxChange (event) {
      this.$emit('input', event.target.checked)
    }
  }
}
</script>

<style scoped>

</style>
