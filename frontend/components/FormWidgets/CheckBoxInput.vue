<template>
  <a-form-item
    :label="label || name"
    :extra="extra"
    :label-col="{ span: 7 }"
    :wrapper-col="{ span: 12 }"
  >
    <a-checkbox
      v-decorator="decorator"
      :checked="value"
      @change="onCheckBoxChange"
    >
    </a-checkbox>
  </a-form-item>
</template>

<script>
export default {
  name: 'CheckBoxInput',
  props: ['label', 'name', 'value', 'extra'],
  computed: {
    decorator () {
      return [
        this.name, {
          rules: [{required: this.required, message: 'This field is required'}]
        }]
    }
  },
  methods: {
    onCheckBoxChange (event) {
      this.$emit('input', event.target.checked)
    }
  }
}
</script>

<style scoped>

</style>
