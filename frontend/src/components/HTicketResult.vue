<template>
  <a-card v-show="isVisible">
    <component :is="currentComponent" :resultData="ticketResult" :dataLoaded="dataLoaded"></component>
    <a-back-top />
  </a-card>
</template>

<script>
import {HRequest} from '../utils/HRequests'
import ResultHostTable from './ResultHostTable'
import SubTab from './SubTab'

export default {
  name: 'HTicketResult',
  components: {ResultHostTable, SubTab},
  props: ['isVisible', 'ticketId'],
  data () {
    return {
      ticketResult: {},
      dataLoaded: false,
      currentComponent: 'ResultHostTable'
    }
  },
  methods: {
    loadResult () {
      HRequest.get('/api/ticket/' + this.ticketId + '/result').then(
        (response) => {
          this.handleResult(response.data.data)
        }
      )
      // this.handleResult({'sa': {'failed': true, 'succeeded': false, 'description': 'farly long description'}})
    },
    handleResult (data) {
      this.ticketResult = data.result
      this.dataLoaded = true
      if (Object.keys(this.ticketResult).length === 2 && Object.keys(this.ticketResult).includes('tasks')) {
        this.currentComponent = 'SubTab'
      } else this.currentComponent = 'ResultHostTable'
    }
  },
  watch: {
    isVisible: function (to, from) {
      if (to === true) {
        this.loadResult()
      }
    },
    executionId: function (to, from) {
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
