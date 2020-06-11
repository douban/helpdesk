<template>
  <a-spin :spinning="spinning" v-show="isVisible">
    <a-card v-show="isVisible">
      <component :is="currentComponent" v-bind:resultData="ticketResult" v-bind:dataLoaded="dataLoaded" :ticketId="ticketId" :ticketProvider="ticketProvider"></component>
      <a-back-top />
    </a-card>
  </a-spin>
</template>

<script>
import {HRequest} from '../utils/HRequests'
import ResultHostTable from './ResultHostTable'
import SubTab from './SubTab'

export default {
  name: 'HTicketResult',
  components: {ResultHostTable, SubTab},
  props: ['isVisible', 'ticketId', 'ticketProvider'],
  data () {
    return {
      ticketResult: {},
      dataLoaded: false,
      currentComponent: 'ResultHostTable',
      spinning: true
    }
  },
  methods: {
    loadResult () {
      this.spinning = true
      this.dataLoaded = false
      HRequest.get('/api/ticket/' + this.ticketId + '/result').then(
        (response) => {
          this.handleResult(response.data.data)
        }
      ).catch((error) => {
        this.$message.error('Get result error: ' + error.response.data.data.description, 10)
      })
      // this.handleResult({'sa': {'failed': true, 'succeeded': false, 'description': 'farly long description'}})
    },
    handleResult (data) {
      this.ticketResult = data.result
      this.dataLoaded = true
      this.spinning = false
      if (Object.keys(this.ticketResult).length === 2 && Object.keys(this.ticketResult).includes('tasks')) {
        this.currentComponent = 'SubTab'
      } else this.currentComponent = 'ResultHostTable'
    }
  },
  watch: {
    isVisible: function (to) {
      if (to === true) {
        this.loadResult()
      }
    },
    executionId: function () {
      this.resetResult()
    }
  },
  mounted () {
    if (this.isVisible) {
      this.loadResult()
    }
  }
}
</script>

<style scoped>
  .text-wrapper {
    white-space: pre-wrap;
    word-wrap: break-word;
    word-break: break-all;
  }
</style>
