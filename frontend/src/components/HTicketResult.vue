<template>
  <a-card v-show="isVisible">
    <a-row>
      <h1>{{totalCount}} execution(s) in total , {{successCount}} succeed, {{failedCount}} failed .</h1>
    </a-row>
    <a-table
      :dataSource="results"
      :columns="columns"
      rowKey="id"
      :defaultExpandedRowKeys="defaultExpanedrow">
      <div slot="filterDropdown" slot-scope="{ setSelectedKeys, selectedKeys, confirm, clearFilters, column }" class='custom-filter-dropdown'>
        <a-input
          v-ant-ref="c => searchInput = c"
          :placeholder="`Search ${column.dataIndex}`"
          :value="selectedKeys[0]"
          @change="e => setSelectedKeys(e.target.value ? [e.target.value] : [])"
          @pressEnter="() => handleSearch(selectedKeys, confirm)"
          style="width: 188px; margin-bottom: 8px; display: block;"
        />
        <a-button
          type='primary'
          @click="() => handleSearch(selectedKeys, confirm)"
          icon="search"
          size="small"
          style="width: 90px; margin-right: 8px"
        >Search</a-button>
        <a-button
          @click="() => handleReset(clearFilters)"
          size="small"
          style="width: 90px"
        >Reset</a-button>
      </div>
      <a-icon slot="filterIcon" slot-scope="filtered" type='search' :style="{ color: filtered ? '#108ee9' : undefined }" />
      <template slot="expandedRowRender" slot-scope="record" style="margin: 0">
        <span v-show="record.traceback !== '' && record.traceback !== undefined">
          <h3><b>traceback:</b></h3>
          <pre class="text-wrapper">{{record.traceback}}</pre>
        </span>
        <span>
          <h3>stderr: </h3>
          <pre class="text-wrapper">{{record.stderr}}</pre>
        </span>
        <span>
          <h3>stdout: </h3>
          <pre class="text-wrapper">{{record.stdout}}</pre>
        </span>
      </template>
      <template slot="status" slot-scope="text">
        <span v-if="text==='Success'"><a-tag color="green">Success</a-tag></span>
        <span v-else><a-tag color="red">Failed</a-tag></span>
      </template>
    </a-table>
    <a-back-top />
  </a-card>
</template>

<script>
import {HRequest} from '../utils/HRequests'

export default {
  name: 'HTicketResult',
  props: ['isVisible', 'ticketId'],
  data () {
    return {
      results: [{}],
      filtered: {},
      successCount: 0,
      failedCount: 0,
      totalCount: 0,
      defaultExpanedrow: [1],
      columns: [
        {
          title: 'Host',
          dataIndex: 'name',
          key: 'name',
          scopedSlots: {
            filterDropdown: 'filterDropdown',
            filterIcon: 'filterIcon',
            customRender: 'customRender'
          },
          onFilter: (value, record) => record.name.toLowerCase().includes(value.toLowerCase()),
          onFilterDropdownVisibleChange: (visible) => {
            if (visible) {
              setTimeout(() => {
                this.searchInput.focus()
              }, 0)
            }
          }
        },
        {
          title: 'Status',
          dataIndex: 'status',
          filters: [
            {text: 'Success', value: 'Success'},
            {text: 'Failed', value: 'Failed'}
          ],
          scopedSlots: {
            customRender: 'status'
          },
          onFilter: (value, record) => record.status === value
        },
        {
          title: 'Return code',
          dataIndex: 'return_code',
          key: 'return_code'
        }
      ]
    }
  },
  methods: {
    loadResult () {
      HRequest.get('/api/ticket/' + this.ticketId + '/result').then(
        (response) => {
          this.handleResult(response.data.data)
        }
      )
      // this.handleResult({'sa': {'failed': true, 'succeeded': false, 'description': 'farly long description'}})
    },
    handleResult (data) {
      let listData = []
      let count = 0
      let successCount = 0
      let failedCount = 0
      for (let property in data.result) {
        let el = data.result[property]
        count += 1
        el.id = count
        el.name = property
        if (el.succeeded || !el.failed) {
          successCount += 1
          el.status = 'Success'
        } else if (el.succeeded || !el.failed) {
          failedCount += 1
          el.status = 'Failed'
        }
        listData.push(el)
      }
      this.successCount = successCount
      this.failedCount = failedCount
      this.totalCount = count
      this.results = listData
    },
    handleSearch (selectedKeys, confirm) {
      confirm()
      this.searchText = selectedKeys[0]
    },

    handleReset (clearFilters) {
      clearFilters()
      this.searchText = ''
    }
  },
  watch: {
    isVisible: function (to, from) {
      if (to === true) {
        this.loadResult()
      }
    },
    executionId: function (to, from) {
      this.resetResult()
    }
  },
  mounted () {
    if (this.isVisible) {
      this.loadResult()
    }
  }
}
</script>

<style scoped>
  .text-wrapper {
    white-space: pre-wrap;
    word-wrap: break-word;
    word-break: break-all;
  }
</style>
