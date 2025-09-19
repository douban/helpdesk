<template functional>
  <a-tabs type="card" :tab-position="left">
    <a-tab-pane v-for="(value, index) in props.resultData.tasks" :key="index">
      <template slot="tab">
        <a-icon v-if="value.state==='succeeded'" type="check-circle" theme="twoTone" two-tone-color="#52c41a" />
        <a-icon v-if="value.state==='failed'" type="close-circle" theme="twoTone" two-tone-color="#eb2f96" />
        {{ value.name.length > 30 ? value.name.slice(0, 30) + '...': value.name }}
      </template>
      <sub-tab
        v-if="Object.keys(value.result).length === 2 && Object.keys(value.result).includes('tasks')"
        :result-data="value.result">
      </sub-tab>
      <result-host-table v-else :data-loaded="props.dataLoaded" :result-data="value.result" :ticket-id="props.ticketId"></result-host-table>
    </a-tab-pane>
  </a-tabs>
</template>
<script>
import ResultHostTable from './ResultHostTable'
export default {
  components: {ResultHostTable},
  props: ['resultData', 'dataLoaded', 'ticketId', 'ticketProvider']
}
</script>
