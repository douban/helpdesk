<template>
  <a-spin :spinning="spinning" v-show="isVisible">
    <a-card v-show="isDagAvaliable">
      <component :is="dagComponent" v-bind:model-data="diagramData"
      v-on:changed-selection="changedSelection" ref="diag" v-bind:selectedNode='selectedNode'></component>
    </a-card>
    
    <a-card v-show="isVisible">
      <component :is="currentComponent" v-bind:resultData="ticketResult" 
      v-bind:dataLoaded="dataLoaded" :ticketId="ticketId" 
      :ticketProvider="ticketProvider" v-bind:resultActiveKey='activeKey'
      v-on:tabClicked='tabClickHandler'></component>
      <a-back-top />
    </a-card>
  </a-spin>
</template>

<script>
import {HRequest} from '../utils/HRequests'
import ResultHostTable from './ResultHostTable'
import SubTab from './SubTab'
import SubTabNoRecursive from './SubTabNoRecursive'
import Hdag from './Hdag'
import go from 'gojs'

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
  methods: {
    loadResult (callback) {
      if (this.spinning) {
        console.warn("Data is loading already, please wait a moment and retry!")
        return
      }
      this.spinning = true
      this.dataLoaded = false
      HRequest.get('/api/ticket/' + this.ticketId + '/result').then(
        (response) => {
          this.handleResult(response.data.data)
          if (callback) {
            callback(this.spinning, response.data.data, false)
          }
        }
      ).catch((error) => {
        this.$message.error('Get result error: ' + error.response.data.data.description, 10)
        this.spinning = false
        if (callback) {
          callback(this.spinning, error.response.data.data, true)
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
    changedSelection: function(e) {
      var node = e.diagram.selection.first();
      this.activeKey = node.data.key
    },
    // get access to the GoJS Model of the GoJS Diagram
    model: function() { return this.$refs.diag.model(); },

    // tell the GoJS Diagram to update based on the arbitrarily modified model data
    updateDiagramFromData: function() { this.$refs.diag.updateDiagramFromData(); },

    tabClickHandler (key) {
      // update gojs diagram node selection status
      this.selectedNode = key
      // update subtab selected tab
      this.activeKey = key
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
