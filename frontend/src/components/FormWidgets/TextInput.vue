<template>
  <a-form-item
    :label="label || name"
    :extra="extra"
    :label-col="{ span: 5 }"
    :wrapper-col="{ span: 12 }"
  >
    <a-input
      :name="name"
      :value="value"
      @input="$emit('input',$event.target.value)"
      :placeholder="placeholder"
      v-decorator="decorator"
    />
  </a-form-item>
</template>
<script>
export default {
  name: 'TextInput',
  props: ['placeholder', 'label', 'name', 'value', 'required', 'extra'],
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
