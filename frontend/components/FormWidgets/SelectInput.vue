<template>
  <a-form-item
    :label="label || name"
    :extra="extra"
    :label-col="{ span: 7 }"
    :wrapper-col="{ span: 12 }"
  >
    <v-select
      v-decorator="decorator()"
      :name="name"
      :options="options"
      :multiple="multiple"
      :clearable="true"
      :searchable="true"
      :filterable="true"
      :select-on-tab="true"
      :value="value"
      @input="handleInput"
      @keypress.enter.native.prevent=""
    ></v-select>
  </a-form-item>
</template>

<script>
export default {
  name: 'SelectInput',
  props: ['placeholder', 'label', 'name', 'value', 'options', 'required', 'extra', 'multiple'],
  methods: {
    handleInput (event) {
      this.$emit('input', event)
    },
    decorator () {
      return [
        this.name, {
          rules: [{
            required: this.required,
            message: 'This field is required'
          }]
        }]
    }
  }
}
</script>

<style scoped>

</style>
