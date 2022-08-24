<template>
  <a-layout>
    <span>Loading...</span>
    <a-modal v-model="rejectModalVisible" title="Reject reason" ok-text="confirm" cancel-text="cancel" @ok="onReject" @cancel="hideRejectModal">
      <a-input v-model="rejectReason" placeholder="Reject reason" max-length=128 />
    </a-modal>
  </a-layout>
</template>

<script>

export default {
// TODO a new TicketDetail component for ticket detail view
  data () {
    return {
      rejectReason: null,
      rejectModalVisible: false,
      ticketInfo : {}
    }
  },
  async mounted () {
    this.ticketInfo = await this.$axios.get('/api/ticket/' + this.$route.params.id).then(res => {
      return res.data.tickets[0]
    })
    if (this.$route.params.op === "approve") {
      this.onApprove()
    } else if (this.$route.params.op === "reject") {
      this.rejectModalVisible = true
    }
  },
  methods: {
    async loadTickets () {
      const ticketResponse = await this.$axios.get('/api/ticket/' + this.id)
      this.ticketInfo = ticketResponse.data.tickets[0]
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
        this.$message.info('Ticket status is not pending, cannot be rejected.')
        this.$router.push({ name: 'ticket-id', params: { id: this.$route.params.id }})
        this.hideRejectModal()
        return
      }
      this.$axios.post(this.ticketInfo.reject_url, {"reason": this.rejectReason}).then(() => {
        this.$message.info('Ticket rejected.')
        this.$router.push({ name: 'ticket-id', params: { id: this.$route.params.id }})
        this.hideRejectModal()
      }).catch((error) => {
        this.errorAsNotification(
          "Ticket reject failed",
          error.response.data.description
        )
      })
    },
    onApprove () {
      if (this.ticketInfo.status !== "pending") {
        this.$message.info('Ticket status is not pending, cannot be approved.')
        this.$router.push({ name: 'ticket-id', params: { id: this.$route.params.id }})
        return
      }
      this.$axios.post(this.ticketInfo.approve_url, {}).then(() => {
        this.$message.info('Ticket approved.')
        this.$router.push({ name: 'ticket-id', params: { id: this.$route.params.id }})
      }).catch((error) => {
        this.errorAsNotification(
          "Ticket approve failed",
          error.response.data.description
        )
      })
    }
  }
}
</script>

<style scoped>

</style>
