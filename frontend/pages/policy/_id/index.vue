<template>
  <a-layout>
    <a-card>
      <router-link :to="{name: 'policy'}">
        <a-icon type="left" /> <span>Return to list</span>
      </router-link>
      <a-divider></a-divider>
      <a-card title="Basic Info" :style="{ marginTop: '16px' }">
        <a-row><b>Policy Name</b>: {{policyInfo.name}}</a-row>
        <a-row><b>Display</b>: {{policyInfo.display}}</a-row>
        <a-row>
          <a-col :span="12"><b>Created by</b>: {{policyInfo.created_by}}</a-col>
          <a-col :span="12"><b>Created at</b>: {{UTCtoLcocalTime(policyInfo.created_at)}}</a-col>
        </a-row>
        <a-row>
          <a-col :span="12"><b>Updated by</b>: {{policyInfo.submitter}}</a-col>
          <a-col :span="12"><b>Updated at</b>: {{UTCtoLcocalTime(policyInfo.updated_at)}}</a-col>
        </a-row>
        <a-row><b>definition</b>: {{ nodesInfo }}</a-row>
      </a-card>
      <a-card title="Params" :style="{ marginTop: '16px' }">
        <a-row v-for="(value, name, index) in policyInfo.definition" :key="index">
          <b>{{name}}</b>: {{value}}
        </a-row>
      </a-card>
      <!-- <a-card title="Flow Info" :style="{ marginTop: '16px' }">
      <a-steps :space="100" :active="active" finish-status="success">
			<a-step v-for="node in policyInfo.defination.nodes" v-bind:key="node" :title="node.name"></a-step>
		  </a-steps> -->
      <!-- </a-card> -->
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
      return this.policyInfo.definition
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
  }
}
</script>

<style scoped>
  .whiteBackground {
    background: #fff
  }
</style>
