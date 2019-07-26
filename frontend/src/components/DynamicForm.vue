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
import SelectInput from './FormWidgets/SelectInput'
import CheckBoxInput from './FormWidgets/CheckBoxInput'
import AFormItem from 'ant-design-vue/es/form/FormItem'

export default {
  name: 'DynamicForm',
  components: {AFormItem, NumberInput, TextInput, SelectInput, CheckBoxInput},
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
