<template>
  <a-form-item
    :label="label || name"
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
  props: ['placeholder', 'label', 'name', 'value', 'required'],
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
