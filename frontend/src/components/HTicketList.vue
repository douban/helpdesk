<template>
  <h-base>
    <a-table
      :columns="columns"
      :dataSource="displayData"
      class="whiteBackground"
    >
      <router-link
        slot="id"
        slot-scope="text, record"
        :to="{name: 'HTicketDetail', params: {id: record.id}}">
        {{record.id}}
      </router-link>
      <span slot="params" slot-scope="text, record">
        <template v-if="text.length > 50">
          {{text.substring(0,50) + '...'}}<a href="javascript:;" v-on:click="loadParams(record.params)">more</a>
        </template>
        <template v-else>
          {{text}}
        </template>
      </span>
      <a slot="result" slot-scope="text, record" :href="record.execution_result_url">link</a>
      <span slot="status" slot-scope="status">
        <a-tag :key="status" :color="approval_color[status]">{{status}}</a-tag>
      </span>
      <span slot="action" slot-scope="text, record">
        <span v-if="record.is_approved === undefined">
          <a-popconfirm
            title="Sure to approve?"
            @confirm="() => onConfirm(record, 'approved', record.approve_url)"
          >
              <a :href="record.approve_url">approve</a>
          </a-popconfirm>
          <a-divider type="vertical" />
          <a-popconfirm
            title="Sure to reject?"
            @confirm="() => onConfirm(record, 'rejected', record.reject_url)"
          >
            <a :href="record.reject_url">reject</a>
          </a-popconfirm>
          <a-divider type="vertical" />
        </span>

        <a :href="record.api_url">detail</a>
        </span>
    </a-table>
    <a-modal
      title="Params"
      :closable="true"
      @ok="onClose"
      @cancel="onClose"
      :visible="param_detail_visible"
    >
      <p v-for="p in params_in_modal" v-bind:key="p.id">{{p.name}}: {{p.value}}</p>
    </a-modal>
  </h-base>
</template>

<script>
import HBase from '@/components/HBase'
import {cmp} from '../utils/HComparer'
import {HRequest} from '../utils/HRequests'
import {getElementFromArray} from '../utils/HFinder'

export default {
// TODO a new TicketDetail component for ticket detail view
  name: 'HTicketList',
  components: {
    HBase
  },
  data () {
    return {
      table_data: [],
      filtered: {},
      approval_color: {'approved': 'green', 'rejected': 'red', 'pending': 'orange'},
      param_detail_visible: false,
      params_in_modal: []
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
        dataIndex: 'display_params',
        sorter: (a, b) => cmp(a, b, 'display_params'),
        scopedSlots: { customRender: 'params' }
      }, {
        title: 'Reason',
        key: 'reason',
        dataIndex: 'reason',
        sorter: (a, b) => cmp(a, b, 'reason')
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
        sorter: (a, b) => cmp(a, b, 'created_at')
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
        sorter: (a, b) => cmp(a, b, 'executed_at')
      },
      {
        title: 'Action',
        key: 'action',
        width: 230,
        scopedSlots: { customRender: 'action' }
      }
      ]
    },
    displayData () {
      if (this.$route.params.id === undefined) {
        return this.table_data
      }
      let selectedData = getElementFromArray(this.table_data, 'id', this.$route.params.id)
      return [selectedData]
    }
  },
  methods: {
    showDrawer () {
      this.param_detail_visible = true
    },
    onClose () {
      this.param_detail_visible = false
    },
    loadParams (params) {
      this.params_in_modal = []
      let i = 1
      Object.keys(params).forEach(
        (key) => {
          this.params_in_modal.push({id: i, name: key, value: params[key]})
        }
      )
      this.showDrawer()
    },
    loadTickets () {
      HRequest.get('/api/ticket').then(
        (response) => {
          this.handleTicketList(response)
        }
      )
    },
    handleTicketList (response) {
      this.table_data = response.data.data.tickets
    },
    onConfirm (record, status, actionUrl) {
      HRequest.get(actionUrl).then(
        (response) => {
          if (response.status === 200) {
            this.$message.success(response.data)
          } else this.$message.warning(response.data)
        }
      )
    }
  },
  mounted () {
    this.loadTickets()
  }
}
</script>

<style scoped>
.whiteBackground {
  background: #fff
}
</style>
