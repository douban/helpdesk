<template functional>
  <a-tabs type="card">
    <a-tab-pane v-for="(value, index) in props.resultData.tasks" :key="index">
      <template slot="tab">
        <a-icon v-if="value.state==='succeeded'" type="check-circle" theme="twoTone" twoToneColor="#52c41a" />
        <a-icon v-if="value.state==='failed'" type="close-circle" theme="twoTone" twoToneColor="#eb2f96" />
        {{value.name}}
      </template>
      <sub-tab
        v-if="Object.keys(value.result).length === 2 && Object.keys(value.result).includes('tasks')"
        :resultData="value.result">
      </sub-tab>
      <result-host-table v-else v-bind:data-loaded="props.dataLoaded" v-bind:resultData="value.result" :ticketId="props.ticketId"></result-host-table>
    </a-tab-pane>
  </a-tabs>
</template>
<script>
import ResultHostTable from './ResultHostTable'
export default {
  components: {ResultHostTable},
  props: ['resultData', 'dataLoaded', 'ticketId']
}
</script>
