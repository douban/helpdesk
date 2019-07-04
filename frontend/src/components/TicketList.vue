<template>
  <a-table :columns="columns"
           :dataSource="table_data"
  >
    <template slot="name" slot-scope="text">
      <a href="javascript:;">{{text}}</a>
    </template>
  </a-table>
</template>

<script>
export default {
  // TODO 需要改为 ajax 异步加载
  // TODO 需要有详情的链接
  name: 'TicketList',
  data () {
    return {
      table_data: [{
        key: '1',
        name: 'John Brown',
        money: '￥300,000.00',
        address: 'New York No. 1 Lake Park'
      }, {
        key: '2',
        name: 'Jim Green',
        money: '￥1,256,000.00',
        address: 'London No. 1 Lake Park'
      }, {
        key: '3',
        name: 'Joe Black',
        money: '￥120,000.00',
        address: 'Sidney No. 1 Lake Park'
      }],

      columns: [{
        title: 'Name',
        dataIndex: 'name',
        scopedSlots: { customRender: 'name' }
      },
      {
        title: 'Cash Assets',
        className: 'column-money',
        dataIndex: 'money'
      },
      {
        title: 'Address',
        dataIndex: 'address'
      }]

    }
  }
}
</script>

<style scoped>

</style>
