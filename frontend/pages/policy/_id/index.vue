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
          <a-col :span="12"><b>Created at</b>: {{policyInfo.created_at}}</a-col>
        </a-row>
        <a-row>
          <a-col :span="12"><b>Updated by</b>: {{policyInfo.submitter}}</a-col>
          <a-col :span="12"><b>Updated at</b>: {{policyInfo.updated_at}}</a-col>
        </a-row>
      </a-card>
    </a-card>
  </a-layout>
</template>

<script>
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
