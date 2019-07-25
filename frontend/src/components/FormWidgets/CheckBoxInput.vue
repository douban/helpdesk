<template>
  <a-form-item
    :label="label || name"
    :extra="extra"
    :label-col="{ span: 5 }"
    :wrapper-col="{ span: 12 }"
  >
    <a-checkbox
      @change="onCheckBoxChange"
      :checked="value"
      v-decorator="decorator"
    >
    </a-checkbox>
  </a-form-item>
</template>

<script>
export default {
  name: 'CheckBoxInput',
  props: ['label', 'name', 'value', 'extra'],
  methods: {
    onCheckBoxChange (event) {
      this.$emit('input', event.target.checked)
    }
  },
  computed: {
    decorator () {
      return [
        this.name, {
          rules: [{required: this.required, message: 'This field is required'}]
        }]
    }
  }
}
</script>

<style scoped>

</style>
