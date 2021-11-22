<template>
  <a-form-item
    :label="label || name"
    :extra="extra"
    :label-col="{ span: 5 }"
    :wrapper-col="{ span: 12 }"
  >
    <v-select
      :name="name"
      :options="options"
      :multiple="true"
      :clearable="true"
      :searchable="true"
      :filterable="true"
      :select-on-tab="true"
      :value="selectedValues"
      @input="handleInput"
      @keypress.enter.native.prevent=""
    ></v-select>
    <input v-decorator="decorator()" type='hidden' :value="value"/>
  </a-form-item>
</template>

<script>
export default {
  name: 'SelectInput',
  props: ['placeholder', 'label', 'name', 'value', 'options', 'required', 'extra'],
  data () {
    return {
      selectedValues: []
    }
  },
  watch: {
    value () {
      if (!this.value) {
        this.selectedValues = []
      } else if (this.selectedValues.join(',') !== this.value) {
        this.selectedValues = this.value.split(',')
      }
    }
  },
  methods: {
    handleInput (event) {
      const realValue = event.join()
      this.selectedValues = event
      this.$emit('input', realValue)
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
