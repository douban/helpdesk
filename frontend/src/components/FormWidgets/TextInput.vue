<template>
  <a-form-item
    :label="label"
  >
    <a-input
      :name="name"
      :value="value"
      @input="$emit('input',$event.target.value)"
      :placeholder="placeholder"
    />
  </a-form-item>
</template>
<script>
export default {
  name: 'TextInput',
  props: ['placeholder', 'label', 'name', 'value']
}
</script>
