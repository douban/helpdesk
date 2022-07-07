<template>
  <a-layout>
    <a-card>
      <router-link :to="{name: 'policy'}">
        <a-icon type="left" /> <span>Return to list</span>
      </router-link>
      <a-card :title="policyInfo.name" :style="{ marginTop: '16px' }">
        <a-steps :space="100" >
          <a-step title="Start"  style="margin-top:24px;margin-bottom:24px"></a-step>
          <a-step v-for="node in nodesInfo" :key="node" :title="node.name" :description="node.approvers" style="margin-top:24px;margin-bottom:24px"></a-step>
          <a-step title="End" style="margin-top:24px;margin-bottom:24px"></a-step>
		    </a-steps>
        <a-form layout="inline">
        	<div>
          <a-col :span="12" style="margin-bottom: 24px">
          <a-form-item label="Flow Name">
            <a-input v-model="policyInfo.name" placeholder="input approver flow name" style="width:300px"></a-input>
          </a-form-item>
          </a-col>
          <a-col :span="12" style="margin-bottom: 24px">
          <a-form-item label="Description">
            <a-input v-model="policyInfo.display" placeholder="input description" style="width:300px"></a-input>
          </a-form-item>
          </a-col>
          </div>
          </a-form>
          <a-divider>Nodes</a-divider>
          <a-form v-for="(node, index) in nodesInfo" :key="index" style="margin-bottom: 24px" layout="inline">
          <a-form-item label="name">
	 	        <a-input v-model="node.name" placeholder="input node name"></a-input>
 	        </a-form-item>
          <a-form-item label="desc">
	 	        <a-input v-model="node.desc" placeholder="input node description"></a-input>
 	        </a-form-item>
          <a-form-item label="next">
	 	        <a-input v-model="node.next" placeholder="input next node name"></a-input>
 	        </a-form-item>
          <a-form-item label="approvers">
	 	        <a-input v-model="node.approvers" placeholder="input node approvers"></a-input>
 	        </a-form-item>
          <a-form-item>
		        <a-icon type="plus-circle" @click="addNode"/>
 	        </a-form-item>
 	        <a-form-item v-if="index !== 0">
		        <a-icon type="minus-circle" @click="removeNode(node)"/>
 	        </a-form-item>
        </a-form>
         <div style="text-align: center; margin-top: 32px">
            <a-button type="primary" :disabled="!canSubmit" @click="handleSubmit">Submit</a-button>
            <a-modal
              v-model="showSubmitOK"
              title="Submit success!"
              ok-text="Go detail"
              cancel-text="Submit another"
              @ok="gotoTicketDetail"
              @cancel="showSubmitOK = false">
              <p>You can stay here to submit another one</p>
            </a-modal>
        </div>
      </a-card>
    </a-card>
  </a-layout>
</template>

<script>

import {UTCtoLcocalTime} from '@/utils/HDate'
export default {
// TODO a new TicketDetail component for ticket detail view
  data () {
    return {
      table_data: [{}],
      filtered: {},
      loadingIntervalId: null,
      canSubmit: true,
      autoRefreshOn: false,
      autoRefreshDisabled: false,
      autoRefreshBtnText: 'Auto Refresh OFF',
      autoRefreshBtnUpdateTimer: null,
      isRefreshing: false,
    }
  },
  computed: {
    policyInfo () {
      return this.table_data[0]
    },
    nodesInfo () {
      const nodes = "nodes"
      if (this.policyInfo.definition) {
        if (this.policyInfo.definition[nodes]) {
          return this.policyInfo.definition[nodes]
        }
      }
      return []
    }
  },
  watch: {
    '$route' () {
      this.loadPolicy()
    }
  },
  mounted () {
    this.loadPolicy()
  },
  methods: {
    UTCtoLcocalTime,
    loadPolicy () {
      this.$axios.get('/api/policies/' + this.$route.params.id).then(
        (response) => {
          this.table_data = response.data.policies
        })
    },
    handleSubmit () {
      const data = {"name": this.policyInfo.name, "display": this.policyInfo.display, "definition": {nodes: this.nodesInfo}}
      this.$axios.post('/api/policies/' + this.$route.params.id, data).then(
        (response) => {
          this.table_data = response.data.policies
          this.$message.success("update success!")
        }).catch((e) => {
          this.$message.warning(JSON.stringify(e))
        })
      this.loadPolicy()
    },
      onSubmit (e, index) {
      e.preventDefault()
      this.$axios.post(this.url_param_rule_add, this.paramRules[index]).then((response) => {
        if (response.data && response.data.id) {
          this.paramRules[index].id = response.data.id
        }
        this.$message.success(JSON.stringify(response.data))
        if (this.paramRules.length - 1 === index) {
          this.paramRules.push({})
        }
      }).catch((e) => {
        this.$message.warning(JSON.stringify(e))
      })
    },
	  addNode() { 
		  this.nodesInfo.push({
        name: '',
        next: '',
        desc: '',
        approvers: ''})
    },
    removeNode(node) {
		  const index = this.nodesInfo.indexOf(node);
		  if(index !== -1) {
			  this.nodesInfo.splice(index, 1);
		  }
	  }
  }
}
</script>

<style scoped>
  .whiteBackground {
    background: #fff
  }
</style>
