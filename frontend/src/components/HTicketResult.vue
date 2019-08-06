<template>
  <a-card v-show="isVisible">
    <a-row>
      {{ticketId}}
    </a-row>
    <a-table :dataSource="results" :columns="columns">
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
          <pre>{{record.traceback}}</pre>
        </span>
        <span>
          <h3>stderr: </h3>
          <pre>{{record.stderr}}</pre>
        </span>
        <span>
          <h3>stdout: </h3>
          <pre>{{record.stdout}}</pre>
        </span>
      </template>
    </a-table>
    <a-row v-for="(value, name) in results" :key="name">
      {{name}} : {{value}}
    </a-row>
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
          }},
        {
          title: 'Succeeded',
          dataIndex: 'succeeded',
          key: 'succeeded'
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
      HRequest.get('/api/execution/1').then(
        (response) => {
          this.handleResult(response.data)
        }
      )
      // this.handleResult({'sa': {'failed': true, 'succeeded': false, 'description': 'farly long description'}})
    },
    handleResult (data) {
      console.log(data)
      let listData = []
      for (let property in data.result) {
        let el = data.result[property]
        el.name = property
        listData.push(el)
      }
      this.results = listData
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
  }
}
</script>

<style scoped>

</style>
