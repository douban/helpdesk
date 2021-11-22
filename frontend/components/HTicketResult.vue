<template>
  <a-spin v-show="isVisible" :spinning="spinning">
    <a-card v-show="isDagAvaliable">
      <component :is="dagComponent" ref="diag"
      :model-data="diagramData" :selected-node='selectedNode' @changed-selection="changedSelection"></component>
    </a-card>

    <a-card v-show="isVisible">
      <component :is="currentComponent" :result-data="ticketResult"
      :data-loaded="dataLoaded" :ticket-id="ticketId"
      :ticket-provider="ticketProvider" :result-active-key='activeKey'
      @tabClicked='tabClickHandler'></component>
      <a-back-top />
    </a-card>
  </a-spin>
</template>

<script>
import go from 'gojs'
import ResultHostTable from './ResultHostTable'
import SubTab from './SubTab'
import SubTabNoRecursive from './SubTabNoRecursive'
import Hdag from './Hdag'

export default {
  name: 'HTicketResult',
  components: {ResultHostTable, SubTab, Hdag, SubTabNoRecursive},
  props: ['isVisible', 'ticketId', 'ticketProvider'],
  data () {
    return {
      ticketResult: {},
      dataLoaded: false,
      currentComponent: 'ResultHostTable',
      dagComponent: 'Hdag',
      spinning: false,
      isDagAvaliable: false,
      diagramData: {
        nodeDataArray: [],
        linkDataArray: []
      },
      activeKey: "",
      selectedNode: "",
    }
  },
  watch: {
    isVisible (to) {
      if (to === true) {
        this.loadResult()
      }
    },
    executionId () {
      this.resetResult()
    }
  },
  mounted () {
    if (this.isVisible) {
      this.loadResult()
    }
  },
  methods: {
    loadResult (callback) {
      if (this.spinning) {
        console.warn("Data is loading already, please wait a moment and retry!")
        return
      }
      this.spinning = true
      this.dataLoaded = false
      this.$axios.get('/api/ticket/' + this.ticketId + '/result').then(
        (response) => {
          this.handleResult(response.data)
          if (callback) {
            callback(this.spinning, response.data, false)
          }
        }
      ).catch((error) => {
        this.$message.error('Get result error: ' + error.response.data.description, 10)
        this.spinning = false
        if (callback) {
          callback(this.spinning, error.response.data, true)
        }
      })
      // this.handleResult({'sa': {'failed': true, 'succeeded': false, 'description': 'farly long description'}})
    },
    handleResult (data) {
      this.ticketResult = data.result
      this.dataLoaded = true
      this.spinning = false

      if (!data.graph) {
        this.isDagAvaliable = false
      } else {
        this.isDagAvaliable = true
        this.dagComponent = 'Hdag'
        this.diagramData = go.Model.fromJson(JSON.stringify(data.graph))
      }

      // 如果有dag属性的直接使用dag+tab展示
      if (this.isDagAvaliable) {
        this.currentComponent = 'SubTabNoRecursive'
        if (data.result.tasks) {
          this.activeKey = data.result.tasks[0].id
        }
      } else if (Object.keys(this.ticketResult).length === 2 && Object.keys(this.ticketResult).includes('tasks')) {
        this.currentComponent = 'SubTab'
      } else {
        this.currentComponent = 'ResultHostTable'
      }
    },
    changedSelection(e) {
      const node = e.diagram.selection.first();
      this.activeKey = node.data.key
    },
    // get access to the GoJS Model of the GoJS Diagram
    model() { return this.$refs.diag.model(); },

    // tell the GoJS Diagram to update based on the arbitrarily modified model data
    updateDiagramFromData() { this.$refs.diag.updateDiagramFromData(); },

    tabClickHandler (key) {
      // update gojs diagram node selection status
      this.selectedNode = key
      // update subtab selected tab
      this.activeKey = key
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
