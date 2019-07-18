<template>
  <div>
    <a-menu
      :defaultSelectedKeys="[111]"
      :defaultOpenKeys="[1, 11, 111]"
      mode="inline"
      :inlineCollapsed="collapsed"
    >
      <template v-for="(item, index) in list">
        <!-- 如果要更改此处的自定义渲染, 请同时修改下方 import 的 SubMenu 内的渲染, 以保证一致 -->
        <a-menu-item v-if="!item.children" :key="index">
          <a v-if="item.target_object" :href="'/#/forms/' + item.target_object" >{{item.name}}</a>
          <span v-else>{{item.name}}</span>
        </a-menu-item>
        <sub-menu v-else :menu-info="item" :key="index"/>
      </template>
    </a-menu>
  </div>
</template>

<script>
import SubMenu from './SubMenu'
import {HRequest} from '../utils/HRequests'
import {getElementFromArray} from '../utils/HFinder'

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
          this.list = response.data.data
          // 在其中查找到选中的 action
          let actionName = this.$route.params.name
          let e = getElementFromArray(response.data.data.action_tree, 'name', actionName)
          console.log(e)
        }
      )
    }
  },
  mounted () {
    this.loadActionTree()
  }
}
</script>
