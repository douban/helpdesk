<template>
  <div>
    <a-modal :visible="prettyLogVisible" title="log" ok-text="confirm" cancel-text="cancel" @ok="onConfirm" @cancel="onCancel" width="85%" id="prettyLogModal">
      <result-host-table v-bind:data-loaded="prettyLogLoaded" v-bind:resultData="prettyLogResult" 
          :ticketId="ticketId"></result-host-table>
    </a-modal>

    <a-tabs type="card" :tabPosition="'left'" :activeKey="resultActiveKey" @tabClick='tabClickHandler'>
      <a-tab-pane v-for="value of resultData.tasks" :key="value.id">
        <template slot="tab">
          {{ value.name.length > 30 ? value.name.slice(0, 30) + '...': value.name }}
        </template>
        <result-host-table v-bind:data-loaded="dataLoaded" v-bind:resultData="value.result" 
        :ticketId="ticketId" @showPrettyLog="showPrettyLog"></result-host-table>
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
