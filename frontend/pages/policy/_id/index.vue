<template>
  <a-layout>
    <a-card>
      <router-link :to="{name: 'policy'}">
        <a-icon type="left" /> <span>Return to list</span>
      </router-link>
      <a-divider></a-divider>
      <a-card title="Info" :style="{ marginTop: '16px' }">
        <a-row><b>Policy Name</b>: {{ policyInfo.name }}</a-row>
        <a-row><b>Display</b>: {{ policyInfo.display }}</a-row>
        <a-row>
          <a-col :span="12"><b>Created by</b>: {{policyInfo.created_by}}</a-col>
          <a-col :span="12"><b>Created at</b>: {{UTCtoLcocalTime(policyInfo.created_at)}}</a-col>
        </a-row>
        <a-row>
          <a-col :span="12"><b>Updated by</b>: {{policyInfo.submitter}}</a-col>
          <a-col :span="12"><b>Updated at</b>: {{UTCtoLcocalTime(policyInfo.updated_at)}}</a-col>
        </a-row>
        <a-row><b>Definition</b>: </a-row>
        <a-steps :space="100" >
          <a-step title="Start"  style="margin-top:24px;margin-bottom:24px"></a-step>
          <a-step v-for="node in nodesInfo" :key="node" :title="node.name" style="margin-top:24px;margin-bottom:24px"></a-step>
          <a-step title="End" style="margin-top:24px;margin-bottom:24px"></a-step>
		    </a-steps>
        <a-form v-for="(node, index) in nodesInfo"
              :key="index"
              method="POST"
              layout="vertical"
              hide-required-mark
              @submit="(e) => onSubmit(e, index)">
        <a-row>
          <a-col :span="10" style="float:left">
            <a-form-item label="Node Name">
              <a-input v-model="node.name" name="name" placeholder="Untitled"></a-input>
            </a-form-item>
          </a-col>
          <a-col :span="10" style="float:right">
            <a-form-item label="Next Node">
              <a-input v-model="node.next" name="next" placeholder='Untitled'></a-input>
            </a-form-item>
          </a-col>
        </a-row>
        <a-row>
          <a-col :span="10" style="float:left">
            <a-form-item label="Description"  label-width="100px">
              <a-textarea v-model="node.desc" name="desc" placeholder='Untitled'></a-textarea>
            </a-form-item>
          </a-col>
          <a-col :span="10" style="float:right">
            <a-form-item label="Approvers">
              <a-input v-model="node.approvers" name="approvers"
                       placeholder="Approver names seperated by comma"
              ></a-input>
    
            </a-form-item>
            </a-col>
        </a-row>
      </a-form>
        <a-button type="medium" shape="circle" style="margin-top" icon="plus" @click="addNode"/>

        <a-button type="primary" :disabled="!canSubmit" >Submit</a-button>
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
    updatePolicy () {
      this.$axios.get('/api/policies/' + this.$route.params.id).then(
        (response) => {
          this.table_data = response.data.policies
        })
    },
    addNode () {
      this.dialogForm = true
      this.List.push ({name: '', next: '', desc: '', approvers: ''})
    }
  }
}
</script>

<style scoped>
  .whiteBackground {
    background: #fff
  }
</style>
