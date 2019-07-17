<template>
  <a-form-item
    :label="label"
  >
    <a-select
      showSearch
      :placeholder="placeholder"
      optionFilterProp="children"
      style="width: 200px"
      @change="handleChange"
      :filterOption="filterOption"
    >
      <a-select-option v-for="c in choices" v-bind:key="c.id" :value="c.value">{{c.display || c.value}}</a-select-option>
    </a-select>
  </a-form-item>
</template>

<script>
export default {
  name: 'ChoiceInput',
  props: ['placeholder', 'label', 'name', 'value', 'choices'],
  methods: {
    filterOption (input, option) {
      return option.componentOptions.children[0].text.toLowerCase().indexOf(input.toLowerCase()) >= 0
    },
    handleChange (event) {
      this.$emit('input', event)
    }
  }
}
</script>

<style scoped>

</style>
