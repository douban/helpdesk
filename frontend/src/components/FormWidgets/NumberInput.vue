<template>
  <a-form-item
    v-bind:label="label"
  >
    <a-input
      v-bind:placeholder="placeholder"
      v-model="value"
      @input="$emit('input',$event.target.value)"
    />
  </a-form-item>
</template>
<script>
export default {
  name: 'NumberInput',
  props: ['placeholder', 'label', 'name', 'value']
}
</script>
