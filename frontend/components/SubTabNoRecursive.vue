<template>
  <div>
    <a-modal id="prettyLogModal" :visible="prettyLogVisible" title="log" ok-text="confirm" cancel-text="cancel" width="85%" @ok="onConfirm" @cancel="onCancel">
      <result-host-table :data-loaded="prettyLogLoaded" :result-data="prettyLogResult" 
          :ticket-id="ticketId"></result-host-table>
    </a-modal>

    <a-tabs type="card" :tab-position="'left'" :active-key="resultActiveKey" @tabClick='tabClickHandler'>
      <a-tab-pane v-for="value of resultData.tasks" :key="value.id">
        <template slot="tab">
          {{ value.name.length > 30 ? value.name.slice(0, 30) + '...': value.name }}
        </template>
        <result-host-table :data-loaded="dataLoaded" :result-data="value.result" 
        :ticket-id="ticketId" @showPrettyLog="showPrettyLog"></result-host-table>
      </a-tab-pane>
    </a-tabs>
  </div>
</template>
<script>
import ResultHostTable from './ResultHostTable'
export default {
  components: {ResultHostTable},
  props: ['resultData', 'dataLoaded', 'ticketId', 'ticketProvider', 'resultActiveKey'],
  data () {
    return {
      prettyLogVisible: false,
      prettyLogLoaded: false,
      prettyLogResult: {},
    }
  },
  methods: {
      tabClickHandler (key) {
          this.$emit('tabClicked', key)
      },

      showPrettyLog(data) {
        this.prettyLogVisible = true
        this.prettyLogLoaded = true
        this.prettyLogResult = data.pretty_log
      },

      onConfirm() {
        this.prettyLogVisible = false
        this.prettyLogLoaded = false
      },

      onCancel() {
        this.prettyLogVisible = false
        this.prettyLogLoaded = false
      }


  }
}
</script>
