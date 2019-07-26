<template>
  <a-form-item
    :label="label"
    :label-col="{ span: 5 }"
    :wrapper-col="{ span: 12 }"
  >
    <a-input
      :placeholder="placeholder"
      :value="value"
      @input="$emit('input',$event.target.value)"
      v-decorator="decorator"
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
        }]
    }
  }
}
</script>
