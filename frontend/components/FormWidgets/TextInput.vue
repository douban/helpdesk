<template>
  <a-form-item
    :label="label || name"
    :extra="extra"
    :label-col="{ span: 7 }"
    :wrapper-col="{ span: 12 }"
  >
    <a-textarea
      v-decorator="decorator"
      :name="name"
      :value="value"
      :placeholder="placeholder"
      auto-size
      @input="$emit('input',$event.target.value)"
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
