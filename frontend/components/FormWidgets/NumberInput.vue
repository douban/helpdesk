<template>
  <a-form-item
    :label="label"
    :label-col="{ span: 7 }"
    :wrapper-col="{ span: 12 }"
  >
    <a-input
      v-decorator="decorator"
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
        }]
    }
  }
}
</script>
