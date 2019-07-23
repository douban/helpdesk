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
      :taggable="true"
      :select-on-tab="true"
      @input="handleInput"
      @keypress.enter.native.prevent=""
      :value="selectedValues"
    ></v-select>
    <input type='hidden' :value="value" />
  </a-form-item>
</template>

<script>
import vSelect from 'vue-select'
export default {
  name: 'SelectInput',
  props: ['placeholder', 'label', 'name', 'value', 'options', 'required', 'extra'],
  components: {
    vSelect
  },
  data () {
    return {
      selectedValues: []
    }
  },
  methods: {
    handleInput (event) {
      console.log(event)
      let realValue = event.join()
      this.selectedValues = event
      this.$emit('input', realValue)
    }
  },
  computed: {
    decorator () {
      return [
        this.name, {
          rules: [{required: this.required, message: 'This field is required'}]
        }] || []
    }
  }
}
</script>

<style scoped>

</style>
