<template>
  <div>
    <a-menu
      :defaultSelectedKeys="['1']"
      :defaultOpenKeys="['2']"
      mode="inline"
      :inlineCollapsed="collapsed"
    >
      <template v-for="item in list">
        <a-menu-item v-if="!item.children" :key="item.key">
          <a v-if="item.url" v-bind:href="item.url" >{{item.title}}</a>
          <span v-else>{{item.title}}</span>
        </a-menu-item>
        <sub-menu v-else :menu-info="item" :key="item.key"/>
      </template>
    </a-menu>
  </div>
</template>

<script>
import SubMenu from './SubMenu'
export default {
  components: {
    'sub-menu': SubMenu
  },
  data () {
    return {
      collapsed: false,
      list: [
        {
          key: '1',
          title: '功能导航',
          url: '/#/'
        }, {
          key: '2',
          title: '账号相关',
          children: [
            {
              key: '2.1',
              title: '申请服务器账号/重置密码',
              url: '/#/apply_server_group'
            },
            {
              key: '2.2',
              title: '申请创建分布式文件系统用户目录',
              url: '/#/create_mfs_userhome'
            },
            {
              key: '2.3',
              title: '申请加入用户组'
            }
          ]
        }]
    }
  },
  methods: {
  }
}
</script>
