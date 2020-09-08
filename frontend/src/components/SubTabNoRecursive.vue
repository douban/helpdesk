<template>
  <a-tabs type="card" :tabPosition="'left'" :activeKey="resultActiveKey" @tabClick='tabClickHandler'>
    <a-tab-pane v-for="value of resultData.tasks" :key="value.id">
      <template slot="tab">
        {{ value.name.length > 30 ? value.name.slice(0, 30) + '...': value.name }}
      </template>
      <result-host-table v-bind:data-loaded="dataLoaded" v-bind:resultData="value.result" 
      :ticketId="ticketId"></result-host-table>
    </a-tab-pane>
  </a-tabs>
</template>
<script>
import ResultHostTable from './ResultHostTable'
export default {
  components: {ResultHostTable},
  props: ['resultData', 'dataLoaded', 'ticketId', 'ticketProvider', 'resultActiveKey'],
  methods: {
      tabClickHandler (key) {
          this.$emit('tabClicked', key)
      }
  }
}
</script>
