<template>
  <a-layout>
    <a-layout-content>
      <!-- <div style="text-align: right; margin: 0"> -->
      <a-button type="primary" style="margin-top:16px;margin-bottom:16px" @click="toggleResult">Create</a-button>
      <a-divider type="vertical" />
      <a-button type="primary" style="margin-top:16px;margin-bottom:16px" @click="toggleResult">Associate</a-button>
    <!-- </div> -->
    <a-table
      :columns="columns"
      :data-source="tableData"
      :pagination="pagination"
      :loading="loading"
      row-key="id"
      class="whiteBackground"
    >
      <span slot="action" slot-scope="text, record">
        <NuxtLink :to="{name: 'policy-id', params: {id: record.id}}">detail</NuxtLink>
        <a-divider type="vertical" />
        <NuxtLink :to="{ name: 'action', params: { action: record.provider_object }, query: { backfill: record.id }}">delete</NuxtLink>
        </span>
    </a-table>
    </a-layout-content>
  </a-layout>
</template>

<script>
import {cmp} from '@/utils/HComparer'
import {UTCtoLcocalTime} from '@/utils/HDate'

export default {
  name: 'HPolicyList',
  data () {
    return {
      tableData: [],
      filtered: {},
      loading: false,
      pagination: {
        pageSize: 1
      },
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
        title: 'Name',
        key: 'name',
        dataIndex: 'name',
        sorter: (a, b) => cmp(a, b, 'name')
      }, {
        title: 'Display',
        key: 'display',
        width: 150,
        dataIndex: 'display',
        sorter: (a, b) => cmp(a, b, 'display'),
        scopedSlots: { customRender: 'display' }
      }, {
        title: 'By',
        key: 'created_by',
        dataIndex: 'created_by',
        sorter: (a, b) => cmp(a, b, 'created_by')
      }, {
        title: 'Create Time',
        key: 'created_at',
        dataIndex: 'created_at',
        sorter: (a, b) => cmp(a, b, 'created_at'),
        customRender: (text) => {
          return UTCtoLcocalTime(text)
        }
      }, {
        title: 'Update by',
        key: 'updated_by',
        dataIndex: 'updated_by',
        sorter: (a, b) => cmp(a, b, 'updated_by')
      }, {
        title: 'Update Time',
        key: 'updated_at',
        dataIndex: 'updated_at',
        sorter: (a, b) => cmp(a, b, 'updated_at'),
        customRender: (text) => {
          return UTCtoLcocalTime(text)
        }
      }, {
        title: 'Action',
        key: 'action',
        width: 230,
        scopedSlots: { customRender: 'action' }
      }]
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
    this.loadPolicies(queryParams)
  },
  methods: {
    loadPolicies (params) {
      this.pagination.current = params.page
      this.loading = true
      this.$axios.get('/api/policies', {params}).then(
        (response) => {
          this.handlePolicyList(response)
        }
      )
    },    
    handlePolicyList (response) {
      this.pagination.total = response.data.total
      this.pagination.current = response.data.page
      this.pagination.pageSize = response.data.page_size || "20"
      // pagination.pageSize  and pagination.current are decorated by ```.sync``
      // the following line is vital. dont know why, just do it.
      this.pagination = {...this.pagination}
      this.tableData = response.data.items
      this.loading = false
    },
  }
}
</script>

<style scoped>

</style>
