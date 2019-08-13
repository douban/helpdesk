<template>
  <h-base>
    <a-card>
      <router-link :to="{name: 'HTicketList'}">
        <a-icon type="left" /> <span>Return to list</span>
      </router-link>
      <a-divider></a-divider>
      <a-steps :current="currentStage">
        <a-step key="0">
          <!-- <span slot="title">Finished</span> -->
          <template slot="title">
            Created
          </template>
          <template slot="description">
            by {{ticketInfo.submitter}}<br/>
            at {{UTCtoLcocalTime(ticketInfo.created_at)}}
          </template>
        </a-step>
        <a-step title="Pending" key="1"/>
        <a-step v-if="ticketInfo.status==='rejected'" title="Rejected" key="3">
        </a-step>
        <a-step v-else title="Approved" key="2">
          <template slot="description">
            <span v-if="ticketInfo.is_approved">
              by {{ticketInfo.confirmed_by}}<br/>
              at {{UTCtoLcocalTime(ticketInfo.confirmed_at)}}
            </span>
          </template>
        </a-step>

      </a-steps>
      <a-card title="Basic Info" :style="{ marginTop: '16px' }">
        <a-row><b>Ticket Title</b>: {{ticketInfo.title}}</a-row>
        <a-row><b>Reason</b>: {{ticketInfo.reason}}</a-row>
        <a-row>
          <a-col :span="12"><b>Created by</b>: {{table_data[0].submitter}}</a-col>
          <a-col :span="12"><b>Created at</b>: {{UTCtoLcocalTime(ticketInfo.created_at)}}</a-col>
        </a-row>
        <a-row v-show="ticketInfo.is_approved">
          <a-col :span="12">
            <b>Approved by</b>: {{table_data[0].confirmed_by}}
            <template v-show="ticketInfo.is_auto_approved">(auto approved)</template>
          </a-col>
          <a-col :span="12">
            <b>Approved at</b>: {{UTCtoLcocalTime(ticketInfo.confirmed_at)}}
          </a-col>
        </a-row>
        <a-row v-show="ticketInfo.executed_at">
          <a-col :span="12"><b>Executed at</b>: {{UTCtoLcocalTime(ticketInfo.executed_at)}}</a-col>
        </a-row>
      </a-card>
      <a-card title="Params" :style="{ marginTop: '16px' }">
        <a-row v-for="(value, name, index) in table_data[0].params" :key="index">
          <b>{{name}}</b>: {{value}}
        </a-row>
      </a-card>
      <a-row :style="{ marginTop: '16px' }">
        <a-button-group v-show="showActionButtons">
          <a-button @click="onReject">Reject</a-button>
          <a-button @click="onApprove" type="primary">Approve</a-button>
        </a-button-group>
        <a-button v-show="showResultButton" :style="{ marginLeft: '16px' }" @click="toggleResult">{{resultButtonText}}</a-button>
      </a-row>
      <h-ticket-result :style="{ marginTop: '16px' }" :is-visible="resultVisible" :ticket-id="ticketInfo.id"></h-ticket-result>
    </a-card>
  </h-base>
</template>

<script>
import HBase from '@/components/HBase'
import {HRequest} from '../utils/HRequests'
import {UTCtoLcocalTime} from '../utils/HDate'
import HTicketResult from './HTicketResult'

export default {
// TODO a new TicketDetail component for ticket detail view
  name: 'HTicketDetail',
  components: {
    HTicketResult,
    HBase
  },
  data () {
    return {
      table_data: [{}],
      filtered: {},
      approval_color: {'approved': 'green', 'rejected': 'red', 'pending': 'orange'},
      param_detail_visible: false,
      params_in_modal: [],
      resultButtonText: 'Show results',
      resultVisible: false
    }
  },
  computed: {
    ticketInfo () {
      return this.table_data[0]
    },
    currentStage () {
      switch (this.ticketInfo.status) {
        case 'created':
          return 0
        case 'approved':
          return 2
        case 'pending':
          return 1
        case 'rejected':
          return 2
      }
    },
    showActionButtons () {
      if (this.ticketInfo.status === 'pending' && this.$store.getters.isAdmin) {
        return true
      }
    },
    showResultButton () {
      if (this.ticketInfo.status === 'approved') return true
    }
  },
  methods: {
    loadTickets () {
      HRequest.get('/api/ticket/' + this.$route.params.id).then(
        (response) => {
          this.handleTicketList(response)
        }
      )
    },
    handleTicketList (response) {
      this.table_data = response.data.data.tickets
    },
    onConfirm (record, status, actionUrl) {
      HRequest.post(actionUrl).then(
        (response) => {
          if (response.status === 200) {
            this.$message.success(response.data)
          } else this.$message.warning(response.data)
        }
      )
    },
    UTCtoLcocalTime,
    toggleResult () {
      this.resultVisible = !this.resultVisible
      if (this.resultVisible) {
        this.resultButtonText = 'Hide results'
      } else {
        this.resultButtonText = 'Show results'
      }
    },
    resetResult () {
      this.resultVisible = false
    },
    onReject () {
      HRequest.post(this.ticketInfo.reject_url).then(() => {
        this.loadTickets()
      })
    },
    onApprove () {
      HRequest.post(this.ticketInfo.approve_url).then(() => {
        this.loadTickets()
      })
    }
  },
  mounted () {
    this.loadTickets()
  },
  watch: {
    '$route' (to, from) {
      this.loadTickets()
      this.resetResult()
    }
  }
}
</script>

<style scoped>
  .whiteBackground {
    background: #fff
  }
</style>
