<template>
  <a-form-item
    :label="label || name"
    :extra="extra"
    :label-col="{ span: 5 }"
    :wrapper-col="{ span: 12 }"
  >
    <a-textarea
      :name="name"
      :value="value"
      @input="$emit('input',$event.target.value)"
      :placeholder="placeholder"
      v-decorator="decorator"
      autosize
    />
  </a-form-item>
</template>
<script>
import ATextarea from 'ant-design-vue/es/input/TextArea'
export default {
  name: 'TextInput',
  components: {ATextarea},
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
