<template>
  <a-layout>
    <a-table
      :columns="columns"
      :data-source="tableData"
      :pagination="pagination"
      :loading="loading"
      row-key="id"
      class="whiteBackground"
      @change="handleTableChange"
    >
      <NuxtLink
        slot="id"
        slot-scope="text, record"
        :to="{name: 'ticket-id', params: {id: record.id}}">
        {{record.id}}
      </NuxtLink>
      <span slot="params" slot-scope="text, record"  :style="{'wordWrap':'break-word','wordBreak': 'break-all'}">
        <template v-if="Boolean(text) && text.length >50">
          {{text.substring(0,50) + '...'}}<a href="javascript:;" @click="loadParams(record.params)">more</a>
        </template>
        <template v-else>
          {{text || ''}}
        </template>
      </span>
      <span slot="reason" slot-scope="text"  :style="{'wordWrap':'break-word','wordBreak': 'break-all'}">
          {{text || ''}}
      </span>
      <a slot="result" slot-scope="text, record" :href="record.execution_result_url">link</a>
      <span slot="status" slot-scope="status">
        <a-tag :key="status" :color="approval_color[status]">{{status}}</a-tag>
      </span>
      <span slot="action" slot-scope="text, record">
        <span v-if="record.is_approved === undefined">
          <a-modal v-model="rejectModalVisible" title="Reject reason" ok-text="confirm" cancel-text="cancel" @ok="onConfirm(record, 'rejected', reasonModalRecord.reject_url)" @cancel="hideRejectModal">
              <a-input v-model="rejectReason" placeholder="Reject reason" maxLength:=128 />
          </a-modal>
          <a-popconfirm
            title="Sure to approve?"
            @confirm="() => onConfirm(record, 'approved', record.approve_url)"
          >
              <a :href="record.approve_url">approve</a>
          </a-popconfirm>
          <a-divider type="vertical" />
          <a-popconfirm
            title="Sure to reject?"
            @confirm="() => showRejectModal(record)"
          >
            <a :href="record.reject_url">reject</a>
          </a-popconfirm>
          <a-divider type="vertical" />
        </span>

        <a :href="record.url">detail</a>
        <a-divider type="vertical" />
        <NuxtLink :to="{ name: 'action', params: { action: record.provider_object }, query: { backfill: record.id }}">rerun</NuxtLink>
        </span>
    </a-table>
    <a-modal
      title="Params"
      :closable="true"
      :visible="param_detail_visible"
      @ok="onClose"
      @cancel="onClose"
    >
      <p v-for="p in params_in_modal" :key="p.id">{{p.name}}: {{p.value}}</p>
    </a-modal>
  </a-layout>
</template>

<script>
import {cmp} from '@/utils/HComparer'
import {UTCtoLcocalTime} from '@/utils/HDate'

export default {
  name: 'HTicketList',
  data () {
    return {
      tableData: [],
      filtered: {},
      approval_color: {
        'approved': 'green',
        'rejected': 'red',
        'pending': 'orange',
        'failed': 'red',
        'COMPLETE': 'green',
        'running': 'orange',
        'RUNNING': 'orange',
        'success': 'green',
        'submitted': 'pink',
        'submit_error': 'red',
        'succeeded': 'green'
      },
      param_detail_visible: false,
      loading: false,
      pagination: {
        pageSize: 1
      },
      params_in_modal: [],
      rejectModalVisible: false,
      rejectReason: null,
      reasonModalRecord: null,
    }
  },
  computed: {
    columns () {
      return [{
        title: 'ID',
        key: 'id',
        dataIndex: 'id',
        sorter: (a, b) => cmp(a, b, 'id'),
        scopedSlots: { customRender: 'id' }
      }, {
        title: 'Title',
        key: 'title',
        dataIndex: 'title',
        sorter: (a, b) => cmp(a, b, 'title')
      }, {
        title: 'Params',
        key: 'params',
        width: 150,
        dataIndex: 'display_params',
        sorter: (a, b) => cmp(a, b, 'display_params'),
        scopedSlots: { customRender: 'params' }
      }, {
        title: 'Reason',
        key: 'reason',
        dataIndex: 'reason',
        sorter: (a, b) => cmp(a, b, 'reason'),
        scopedSlots: { customRender: 'reason' }
      }, {
        title: 'Submitter',
        key: 'submitter',
        dataIndex: 'submitter',
        sorter: (a, b) => cmp(a, b, 'submitter')
      }, {
        title: 'Status',
        key: 'status',
        dataIndex: 'status',
        sorter: (a, b) => cmp({'pending': 0, 'approved': 1, 'rejected': 2}[a.status], {'pending': 0, 'approved': 1, 'rejected': 2}[b.status]),
        scopedSlots: { customRender: 'status' },
        filters: [
          {
            text: 'approved',
            value: 'approved'
          }, {
            text: 'rejected',
            value: 'rejected'
          }, {
            text: 'pending',
            value: 'pending'
          }],
        onFilter: (value, record) => record.status === value,
        filteredValue: this.filtered.status
      }, {
        title: 'By',
        key: 'confirmed_by',
        dataIndex: 'confirmed_by',
        sorter: (a, b) => cmp(a, b, 'confirmed_by')
      },
      {
        title: 'Create Time',
        key: 'created_at',
        dataIndex: 'created_at',
        sorter: (a, b) => cmp(a, b, 'created_at'),
        customRender: (text) => {
          return UTCtoLcocalTime(text)
        }
      },
      {
        title: 'Result',
        key: 'result',
        dataIndex: 'execution_result_url',
        sorter: (a, b) => cmp(a, b, 'execution_result_url'),
        scopedSlots: { customRender: 'result' }
      },
      {
        title: 'Execute Time',
        key: 'executed_at',
        dataIndex: 'executed_at',
        sorter: (a, b) => cmp(a, b, 'executed_at'),
        customRender: (text) => {
          return UTCtoLcocalTime(text)
        }
      },
      {
        title: 'Action',
        key: 'action',
        width: 230,
        scopedSlots: { customRender: 'action' }
      }
      ]
    }
  },
  mounted () {
    const queryParams = this.$route.query
    if (queryParams.page === undefined) {
      queryParams.page = 1
    }
    if (queryParams.pagesize === undefined) {
      queryParams.pagesize = 10
    }
    queryParams.page = Number(queryParams.page)
    queryParams.pageSize = Number(queryParams.pageSize || 10)
    this.loadTickets(queryParams)
  },
  methods: {
    showRejectModal (record) {
      this.rejectModalVisible = true
      this.reasonModalRecord = record
      this.rejectReason = null
    },
    hideRejectModal () {
      this.rejectModalVisible = false
    },
    showDrawer () {
      this.param_detail_visible = true
    },
    onClose () {
      this.param_detail_visible = false
    },
    loadParams (params) {
      this.params_in_modal = []
      const i = 1
      Object.keys(params).forEach(
        (key) => {
          this.params_in_modal.push({id: i, name: key, value: params[key]})
        }
      )
      this.showDrawer()
    },
    loadTickets (params) {
      this.pagination.current = params.page
      this.loading = true
      this.$axios.get('/api/ticket', {params}).then(
        (response) => {
          this.handleTicketList(response)
        }
      )
    },
    handleTicketList (response) {
      this.pagination.total = response.data.total
      this.pagination.current = response.data.page
      this.pagination.pageSize = response.data.page_size || "20"
      // pagination.pageSize  and pagination.current are decorated by ```.sync``
      // the following line is vital. dont know why, just do it.
      this.pagination = {...this.pagination}
      this.tableData = response.data.tickets
      this.loading = false
    },
    handleTableChange (pagination, filters, sorter) {
      // sorter example:
      // {
      //   "column": {},
      //   "order": "ascend",
      //   "field": "confirmed_by",
      //   "columnKey": "confirmed_by"
      // }
      // order can be 'descend'
      // filters example:
      // {
      //   "status": [
      //   "rejected"
      // ]
      // }
      const queryParams = {page: pagination.current, pagesize: pagination.pageSize}
      const selectedStatus = filters.status
      if (selectedStatus !== undefined) {
        queryParams.status__in = selectedStatus.join()
      }
      if (sorter.columnKey !== undefined) {
        queryParams.order_by = sorter.columnKey
        if (sorter.order === 'ascend') {
          queryParams.desc = false
        } else {
          queryParams.desc = true
        }
      }
      this.loadTickets(queryParams)
    },
    onConfirm (record, status, actionUrl) {
      let postData = {}
      if (status === "rejected") {
        postData = {"reason": this.rejectReason}
      }
      this.$message.loading('Action in progress..', 2.5)
      this.$axios.post(actionUrl, postData).then(() => {
        this.$message.info('Ticket ' + status)
        this.hideRejectModal()
      }).catch((error) => {
        const rawMsg = error.response.data.description
        const msg = rawMsg.length > 300 ? rawMsg.slice(0, 300) + '... ' : rawMsg
        this.$notification.title = rawMsg
        this.$notification.open({
          message: "Ticket " + status + " failed",
          description: msg + "\norigin url: " + actionUrl,
          duration: 0
        })
      })
    }
  }
}
</script>

<style scoped>
.whiteBackground {
  background: #fff
}
</style>
