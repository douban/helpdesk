<template>
  <div>
    <a-menu
      :defaultSelectedKeys="[111]"
      :defaultOpenKeys="[1, 11, 111]"
      mode="inline"
      :inlineCollapsed="collapsed"
    >
      <template v-for="item in list">
        <!-- 如果要更改此处的自定义渲染, 请同时修改下方 import 的 SubMenu 内的渲染, 以保证一致 -->
        <a-menu-item v-if="!item.children" :key="item.key">
          <a v-if="item.name" :href="'/#/forms/' + item.name" >{{item.title}}</a>
          <span v-else>{{item.title}}</span>
        </a-menu-item>
        <sub-menu v-else :menu-info="item" :key="item.key"/>
      </template>
    </a-menu>
  </div>
</template>

<script>
import SubMenu from './SubMenu'
import {HRequest} from '../utils/HRequests'
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
          title: '功能导航加载中',
          url: '/#/'
        }]
    }
  },
  methods: {
    loadActionTree () {
      HRequest.get('/api/action_tree').then(
        (response) => {
          this.list = response.data.data.action_tree
        }
      )
    }
  },
  mounted () {
    this.loadActionTree()
  }
}
</script>
