<template>
  <div>
    <component :is="getComponent(field)"
               v-for="(field, index) in schema"
               :key="index"
               :value="formData[field.name]"
               v-bind="field"
               @input="updateForm(field.name, $event)">
    </component>
  </div>
</template>

<script>

export default {
  name: 'DynamicForm',
  props: ['schema', 'value'],
  data () {
    return {}
  },
  computed: {
    formData () {
      return this.value || {}
    }
  },
  methods: {
    updateForm (fieldName, v) {
      if (v===false) {
        // bool false value, leave it as is
        this.$set(this.formData, fieldName, v)
      } else if(!v) {
        // empty value, remove it
        this.$delete(this.formData, fieldName)
      } else {
        this.$set(this.formData, fieldName, v)
      }
      this.$emit('input', this.formData)
    },
    getComponent(field) {
      return "FormWidgets" + field.fieldType
    }
  }
}
</script>
