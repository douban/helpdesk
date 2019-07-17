<template>
  <h-base>
    <a-table :columns="columns"
             :dataSource="table_data"
    >
      <a slot="id" slot-scope="text, record" :href="record.url">{{record.id}}</a>
      <span slot="params" slot-scope="text, record">
        {{text}}<a href="javascript:;" v-on:click="loadParams(record.params)">加载更多</a>
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
      title="任务参数详情"
      :closable="false"
      @ok="onClose"
      :visible="param_detail_visible"
    >
      <p v-for="p in params_in_modal" v-bind:key="p.id">{{p.name}}: {{p.value}}</p>
    </a-modal>
  </h-base>
</template>

<script>
import HBase from '@/components/HBase'
import {cmp} from '../utils/HComparer'

export default {
// TODO 需要改为 ajax 异步加载
// TODO 需要有详情的链接
  name: 'TicketList',
  components: {
    HBase
  },
  data () {
    return {
      table_data: [{
        key: 1,
        id: '1',
        title: 'John Brown',
        display_params: 'pubkey: ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDS6PMayCes8wgZh1c0V3PkO2X67kh19JtVHOMrcy8tWqoiYvP/bfhq2uuN/LQaymjpqzCqoZDTSizOyXCnDh58ZqxQnC0XJWHOLDaJzPgXRr5w5cozP5zjCZXJV6huQpypeSbaRkLuPUPlu6DYc45UHWsqaRe0fkT0KkMzDy/Ylp4I8bGa7av1jo4+Wx9yVJyJmWvtXKFhZad6hHVtphBxbow3xFF8TAKyc0YdY7t2cbGSQ4cwqlJUy15futFZlybmf840Yd6hzFTSWpJQ2ecd2baTkA+8DTyRCKV/0A7mqWRXR3rQ+iz3urjfqhqYrKJVXHmubDtl+sUcAM8Rb+vb yaoqian@douban.com; ldap_id: yaoqian'.substring(0, 30),
        params: {
          pubkey: 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDS6PMayCes8wgZh1c0V3PkO2X67kh19JtVHOMrcy8tWqoiYvP/bfhq2uuN/LQaymjpqzCqoZDTSizOyXCnDh58ZqxQnC0XJWHOLDaJzPgXRr5w5cozP5zjCZXJV6huQpypeSbaRkLuPUPlu6DYc45UHWsqaRe0fkT0KkMzDy/Ylp4I8bGa7av1jo4+Wx9yVJyJmWvtXKFhZad6hHVtphBxbow3xFF8TAKyc0YdY7t2cbGSQ4cwqlJUy15futFZlybmf840Yd6hzFTSWpJQ2ecd2baTkA+8DTyRCKV/0A7mqWRXR3rQ+iz3urjfqhqYrKJVXHmubDtl+sUcAM8Rb+vb yaoqian@douban.com',
          ldap_id: 'some_one'
        },
        reason: 'some_reason',
        submitter: 'someone',
        status: 'pending',
        confirmed_by: 'someone2',
        executed_at: 'some_date'
      }],
      some_data: 'asdasdas',
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
    }
  }
}
</script>

<style scoped>

</style>
