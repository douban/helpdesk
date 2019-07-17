<template>
  <div>
    <component v-for="(field, index) in schema"
               :key="index"
               :is="field.fieldType"
               :value="formData[field.name]"
               @input="updateForm(field.name, $event)"
               v-bind="field">
    </component>
  </div>
</template>

<script>
import NumberInput from './FormWidgets/NumberInput'
import TextInput from './FormWidgets/TextInput'
import ChoiceInput from './FormWidgets/ChoiceInput'
import CheckBoxInput from './FormWidgets/CheckBoxInput'

export default {
  name: 'HForm',
  components: {NumberInput, TextInput, ChoiceInput, CheckBoxInput},
  props: ['schema', 'value'],
  data () {
    return {
      formData: this.value || {}
    }
  },
  methods: {
    updateForm (fieldName, value) {
      this.$set(this.formData, fieldName, value)
      this.$emit('input', this.formData)
    }
  }
}
</script>
