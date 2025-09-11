<template>
  <a-form-item
    :label="label || name"
    :extra="extra"
    :label-col="{ span: 7 }"
    :wrapper-col="{ span: 12 }"
  >
    <v-select
      :name="name"
      :options="options"
      :multiple="multiple"
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
  props: ['placeholder', 'label', 'name', 'value', 'options', 'required', 'extra', 'multiple'],
  data () {
    return {
      selectedValues: []
    }
  },
  watch: {
    value () {
      console.log(`watch value: ${this.value}`)
      if (!this.value) {
        this.selectedValues = []
      } else if (!Array.isArray(this.value)){
          this.selectedValues = [this.value]
      }
    }
  },
  methods: {
    handleInput (event) {
      console.log(event)
      let realValue;
      if (!Array.isArray(event)) {
        realValue = [event]
      }
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
