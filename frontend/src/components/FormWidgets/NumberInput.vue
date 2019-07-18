<template>
  <a-form-item
    :label="label"
  >
    <a-input
      :placeholder="placeholder"
      :value="value"
      @input="$emit('input',$event.target.value)"
    />
  </a-form-item>
</template>
<script>
export default {
  name: 'NumberInput',
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
