<template>
  <h-base>
    <a-card>
      <router-link :to="{name: 'HTicketList'}">
        <a-icon type="left" /> <span>Return to list</span>
      </router-link>
      <a-divider></a-divider>
      <a-steps :current="currentStage" :status="currentStatus">
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
          <template slot="description">
            <span v-if="!ticketInfo.is_approved">
              by {{ticketInfo.confirmed_by}}<br/>
              at {{UTCtoLcocalTime(ticketInfo.confirmed_at)}} <br/>
              {{ ticketInfo.reason>150 ? ticketInfo.reason.slice(0, 150) + '...' : ticketInfo.reason }}
            </span>
          </template>
        </a-step>
        <a-step v-else title="Approved" key="2">
          <template slot="description">
            <span v-if="ticketInfo.is_approved">
              by {{ticketInfo.confirmed_by}}<br/>
              at {{UTCtoLcocalTime(ticketInfo.confirmed_at)}}
            </span>
          </template>
        </a-step>
        <a-step title="Submitted" key="4">
          <template slot="description">
            <span v-if="ticketAnnotation.hasOwnProperty('execution_creation_success')"
            :title="ticketAnnotation.execution_creation_msg">
              {{ ticketAnnotation.execution_creation_msg.length>150 ? ticketAnnotation.execution_creation_msg.slice(0, 150) + '...':ticketAnnotation.execution_creation_msg }}<br/>
              at {{UTCtoLcocalTime(ticketInfo.executed_at)}}
            </span>
          </template>
        </a-step>
        <a-step title="Run" key="5">
          <template slot="description">
            <span v-if="ticketAnnotation.hasOwnProperty('execution_status')">
              {{ticketAnnotation.execution_status}}
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
          <a-col :span="12"><b>Executed by</b>: {{ ticketInfo.provider_type }}</a-col>
        </a-row>
      </a-card>
      <a-card title="Params" :style="{ marginTop: '16px' }">
        <a-row v-for="(value, name, index) in table_data[0].params" :key="index">
          <b>{{name}}</b>: {{value}}
        </a-row>
      </a-card>
      <a-row :style="{ marginTop: '16px' }">
        <a-button-group v-show="showActionButtons">
          <a-modal v-model="rejectModalVisible" title="Reject reason" ok-text="confirm" cancel-text="cancel" @ok="onReject" @cancel="hideRejectModal">
              <a-input placeholder="Reject reason" v-model="rejectReason" maxLength:=128 />
          </a-modal>
          <a-button @click="showRejectModal">Reject</a-button>
          <a-button @click="onApprove" type="primary">Approve</a-button>
        </a-button-group>
        <a-button v-show="showResultButton" :style="{ marginLeft: '16px' }" @click="toggleResult">{{resultButtonText}}</a-button>
        <a-button v-show="resultVisible" :style="{ marginLeft: '5px' }" @click="loadTResult">Refresh</a-button>
        
        <a-switch v-show="resultVisible" :style="{ marginLeft: '5px' }" 
          :checked-children="autoRefreshBtnText" 
          :un-checked-children="autoRefreshBtnText"
          :loading="isRefreshing"
          :checked="autoRefreshOn"
          :disabled="autoRefreshDisabled"
          @click="toggleAutoRefresh"
        />
      </a-row>
      <h-ticket-result :style="{ marginTop: '16px' }" :is-visible="resultVisible" :ticket-id="ticketInfo.id" ref="ticketResult" :ticketProvider="ticketInfo.provider_type"></h-ticket-result>
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
      resultVisible: false,
      rejectModalVisible: false,
      statusToStepStatus: {
        'created': {'status': 'finish', 'stepKey': 0},
        'approved': {'status': 'finish', 'stepKey': 2},
        'pending': {'status': 'process', 'stepKey': 1},
        'rejected': {'status': 'error', 'stepKey': 2},
        'submitted': {'status': 'process', 'stepKey': 4},
        'submit_error': {'status': 'error', 'stepKey': 3},
        'running': {'status': 'process', 'stepKey': 5},
        'succeed': {'status': 'finish', 'stepKey': 5},
        'success': {'status': 'finish', 'stepKey': 5},
        'failed': {'status': 'error', 'stepKey': 4},
        'unknown': {'status': 'process', 'stepKey': 4},
        'succeeded': {'status': 'finish', 'stepKey': 4}
      },
      ticketEndStatus: ['rejected', 'submit_error', 'succeed', 'success', 'succeeded', 'failed', 'unknown'],
      rejectReason: null,
      loadingIntervalId: null,
      autoRefreshOn: false,
      autoRefreshDisabled: false,
      autoRefreshBtnText: 'Auto Refresh OFF',
      autoRefreshBtnUpdateTimer: null,
      isRefreshing: false,
    }
  },
  computed: {
    ticketInfo () {
      return this.table_data[0]
    },
    currentStatus () {
      if (this.ticketInfo.status) {
        if (!this.statusToStepStatus[this.ticketInfo.status]) {
          return this.statusToStepStatus['unknown'].status
        }
        return this.statusToStepStatus[this.ticketInfo.status].status
      }
      return "finish"
    },
    currentStage () {
      if (this.ticketInfo.status) {
        if (!this.statusToStepStatus[this.ticketInfo.status]) {
          return this.statusToStepStatus['unknown'].stepKey
        }
        return this.statusToStepStatus[this.ticketInfo.status].stepKey
      }
      return 0
    },
    ticketAnnotation () {
      if (this.ticketInfo.annotation) {
        return this.ticketInfo.annotation
      } else {
        return {'execution_creation_success': false, 'execution_creation_msg': ''}
      }
    },
    showActionButtons () {
      if (this.ticketInfo.status === 'pending' && this.$store.getters.isAdmin) {
        return true
      }
      return false
    },
    showResultButton () {
      if (this.ticketInfo.status) {
        let status = this.ticketInfo.status
        if (!this.statusToStepStatus[this.ticketInfo.status]) {
          status = 'unknown'
        }
        return (this.statusToStepStatus[status].stepKey >=
        this.statusToStepStatus['approved'].stepKey) && this.ticketInfo.status !== 'rejected'
      }
      return false
    }
  },
  methods: {
    loadTickets () {
      HRequest.get('/api/ticket/' + this.$route.params.id).then(
        (response) => {
          this.table_data = response.data.data.tickets
          switch (this.$route.params.action) {
            case 'approve':
              this.onApprove()
              break
            case 'reject':
              this.showRejectModal()
              break
            case undefined:
              break
            default:
              this.$message.warning('Action ' + this.$route.params.action + 'for this ticket is invalid.')
          }
        })
    },
    updateTicket () {
      HRequest.get('/api/ticket/' + this.$route.params.id).then(
        (response) => {
          this.table_data = response.data.data.tickets
        })
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
    errorAsNotification (title, rawMsg) {
      const msg = rawMsg.length > 300 ? rawMsg.slice(0, 300) + '... ' : rawMsg
      this.$notification.title = rawMsg
      this.$notification.open({
        message: title,
        description: msg,
        duration: 0
      })
    },
    showRejectModal () {
      this.rejectModalVisible = true
    },
    hideRejectModal () {
      this.rejectModalVisible = false
    },
    onReject () {
      if (this.ticketInfo.status !== "pending") {
        this.$message.info('Ticket has is not pending, cannot be rejected.')
        this.$router.push({ name: 'HTicketDetail', params: { id: this.$route.params.id }})
        this.hideRejectModal()
        return
      }
      HRequest.post(this.ticketInfo.reject_url, {"reason": this.rejectReason}).then(() => {
        this.updateTicket()
        this.$message.info('Ticket rejected.')
        this.$router.push({ name: 'HTicketDetail', params: { id: this.$route.params.id }})
        this.hideRejectModal()
      }).catch((error) => {
        this.errorAsNotification(
          "Ticket reject failed",
          error.response.data.data.description
        )
      })
    },
    onApprove () {
      if (this.ticketInfo.status !== "pending") {
        this.$message.info('Ticket has is not pending, cannot be approved.')
        this.$router.push({ name: 'HTicketDetail', params: { id: this.$route.params.id }})
        return
      }
      HRequest.post(this.ticketInfo.approve_url).then(() => {
        this.updateTicket()
        this.$message.info('Ticket approved.')
        this.$router.push({ name: 'HTicketDetail', params: { id: this.$route.params.id }})
      }).catch((error) => {
        this.errorAsNotification(
          "Ticket approve failed",
          error.response.data.data.description
        )
      })
    },
    loadTResult (e, callback) {
      this.loadTickets()
      this.$refs.ticketResult.loadResult(callback)
    },
    isTicketEndStatus() {
      const ticketStatus = this.ticketInfo.status
      return (ticketStatus 
          && this.statusToStepStatus[ticketStatus] 
          && this.ticketEndStatus.includes(ticketStatus))
    },
    notifyFinishedTicket() {
      this.$notification.open({
        message: 'This ticket is in final status',
        description: 'Ticket has been marked as final status, refresh is invailed.',
        duration: 0
      })
    },
    toggleAutoRefresh (checked) {
      if (checked && !this.autoRefreshOn) {
        this.autoRefreshOn = true
        this.autoRefreshBtnText = "Auto Refresh On"
        const interval = 10000
        const maxAutoRefreshTry = 360  // 1 hour
        let tried = 0
        let passedTime = 0
        this.loadingIntervalId = setInterval(() => {
          // prevent muiltiple refresh 
          if (this.isRefreshing) {
            this.autoRefreshBtnText = 'Refreshing ...'
            return
          }

          // update clockdown in switch
          if (passedTime <= interval) {
            this.autoRefreshBtnText = "Refresh after " + (interval - passedTime) / 1000 + " s ..."
            passedTime += 1000
          } else {
            this.isRefreshing = true
            tried += 1
            this.loadTResult(null, (isRefreshGoing, resp, isError) => {
              this.isRefreshing = isRefreshGoing
              if (isError || this.isTicketEndStatus() || tried > maxAutoRefreshTry) {
                clearInterval(this.loadingIntervalId)
                const finished = this.isTicketEndStatus()
                const isMaxRefreshExceeded = tried > maxAutoRefreshTry
                this.autoRefreshBtnText = finished ? "Finished" : (isMaxRefreshExceeded ? "Max Refresh Try Exceeded" : "Error")
                
                if (finished) {
                  this.notifyFinishedTicket()
                } else {
                  this.$notification.open({
                    message: isMaxRefreshExceeded ? 'Auto Refresh tried exceeded ' + maxAutoRefreshTry + ' times' : 'Ticket result load error',
                    description: isMaxRefreshExceeded ? '' : resp.description,
                    duration: 0
                  })
                }
                this.autoRefreshOn = false
                this.autoRefreshDisabled = isMaxRefreshExceeded ? false : true
                this.isRefreshing = false
              }
            } )
            passedTime = 0
          }
        }, 1000)
      } else {
        clearInterval(this.loadingIntervalId)
        this.autoRefreshBtnText = "Auto Refresh OFF"
        this.autoRefreshOn = false
      }
       
    }
  },
  mounted () {
    this.loadTickets()
  },
  watch: {
    '$route' () {
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
