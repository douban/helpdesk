<template>
  <div>
    <a-row>
      <h1>{{totalCount}} execution(s) in total , {{successCount}} succeed, {{failedCount}} failed .</h1>
    </a-row>
    <a-table
      :data-source="results"
      :columns="columns"
      :row-key="handleRowKey"
      :pagination="paginationConfig"
      @expand="handleRowExpand">
      <div slot="filterDropdown" slot-scope="{ setSelectedKeys, selectedKeys, confirm, clearFilters, column }" class='custom-filter-dropdown'>
        <a-input
          v-ant-ref="c => searchInput = c"
          :placeholder="`Search ${column.dataIndex}`"
          :value="selectedKeys[0]"
          style="width: 188px; margin-bottom: 8px; display: block;"
          @change="e => setSelectedKeys(e.target.value ? [e.target.value] : [])"
          @pressEnter="() => handleSearch(selectedKeys, confirm)"
        />
        <a-button
          type='primary'
          icon="search"
          size="small"
          style="width: 90px; margin-right: 8px"
          @click="() => handleSearch(selectedKeys, confirm)"
        >Search</a-button>
        <a-button
          size="small"
          style="width: 90px"
          @click="() => handleReset(clearFilters)"
        >Reset</a-button>
      </div>
      <a-icon slot="filterIcon" slot-scope="filtered" type='search' :style="{ color: filtered ? '#108ee9' : undefined }" />
      <template slot="expandedRowRender" slot-scope="record" style="margin: 0">
        <a-spin :spinning="spinning">
          <span v-show="record.traceback !== '' && record.traceback !== undefined">
            <h3><b>traceback:</b></h3>
            <pre class="text-wrapper">{{record.traceback}}</pre>
          </span>
          <span>
            <h3>stderr: </h3>
            <pre class="text-wrapper">
              <text-highlight :queries='highlightQueries' :highlight-style='highlightStyle'>
                {{typeof(record.stderr) === 'string' ? record.stderr : ''}}
              </text-highlight>
            </pre>
          </span>
          <span>
            <h3>stdout: </h3>
            <pre class="text-wrapper">{{typeof(record.stdout) === 'string' ? record.stdout : ''}}</pre>
          </span>
        </a-spin>
      </template>
      <template slot="status" slot-scope="text">
        <span v-if="text==='Success'"><a-tag color="green">Success</a-tag></span>
        <span v-else><a-tag color="red">Failed</a-tag></span>
      </template>
    </a-table>
  </div>
</template>

<script>

export default {
  name: 'ResultHostTable',
  props: ['resultData', 'dataLoaded', 'ticketId'],
  data () {
    return {
      spinning: false,
      highlightQueries: [],
      highlightStyle: {color: 'green', 'background': 'yellow'},
      results: [{}],
      filtered: {},
      successCount: 0,
      failedCount: 0,
      totalCount: 0,
      defaultExpanedrow: [1],
      paginationConfig: {
        pageSizeOptions: ['100', '200', '500'],
        defaultPageSize: 100,
        showSizeChanger: true
      },
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
  watch: {
    dataLoaded () {
      this.loadResult()
    }
  },
  mounted () {
    if (this.dataLoaded === true) {
      this.loadResult()
    }
  },
  methods: {
    loadResult () {
      this.handleResult(this.resultData)
      // this.handleResult({'sa': {'failed': true, 'succeeded': false, 'description': 'farly long description'}})
    },
    handleResult (data) {
      const listData = []
      let count = 0
      let successCount = 0
      let failedCount = 0
      this.highlightQueries = []
      for (const property in data) {
        const el = data[property]
        count += 1
        el.id = count
        el.name = property
        if (el.succeeded || !el.failed) {
          successCount += 1
          el.status = 'Success'
        } else if (el.failed || !el.succeeded) {
          failedCount += 1
          el.status = 'Failed'
        } else {
          // Unknown count as failed
          failedCount += 1
          el.status = 'Failed'
        }
        listData.push(el)

        if (el.highlight_queries) {
          for (const r of el.highlight_queries) {
            const re = new RegExp(r)
            if (!this.highlightQueries.includes(re)) {
              this.highlightQueries.push(re)
            }
          }
        }
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
    },

    handleFormattedLog(prettyLog) {
      switch (prettyLog.formatter) {
      case 'ASYNC_SSH_OPERATOR_FORMATTER':
        // show async op formatter model
        this.$emit('showPrettyLog', prettyLog)
        break
      default:
        console.error("pretty log formatter" + prettyLog.formatter + "have no frontend suppport!")
      }
    },

    handleRowExpand (expanded, record) {
      if (expanded && (record.stdout.output_load || record.stderr.output_load)) {
        const std = {
          'stdout': record.stdout.output_load,
          'stderr': record.stderr.output_load
        }

        for (const io in std) {
          if (std[io]) {
            this.spinning = true
            const queryString = io === 'stdout' ? record.stdout.query_string : record.stderr.query_string
            this.$axios.get('/api/ticket/' + this.ticketId + '/result' + queryString).then(
              (response) => {
                // if pretty log then show model
                if (response.data.pretty_log) {
                  const prettyLog = response.data.pretty_log[0]
                  if (prettyLog) {
                    this.handleFormattedLog(prettyLog)
                    record.prettyLog = prettyLog
                  }
                }
                const output = response.data[0] ? response.data[0] : response.data.message[0]
                if (io === 'stdout') {
                  record.stdout = output
                } else {
                  record.stderr = output
                }
                this.spinning = false
              }
            )
          }
        }
      }

      if (expanded && record.prettyLog) {
        this.handleFormattedLog(record.prettyLog)
      }
    },

    handleRowKey (record) {
      return 'tickets-result-' + record.id
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
