<template>
  <div>
    <a-menu
      v-model="SelectedKeys"
      :defaultOpenKeys="OpenKeys"
      mode="inline"
      :inlineCollapsed="collapsed"
    >
      <template v-for="item in list">
        <!-- 如果要更改此处的自定义渲染, 请同时修改下方 import 的 SubMenu 内的渲染, 以保证一致 -->
        <a-menu-item v-if="!item.children" :key="item.name">
          <a v-if="item.target_object" :href="'/#/forms/' + item.target_object" >{{item.name}}</a>
          <span v-else>{{item.name}}</span>
        </a-menu-item>
        <sub-menu v-else :menu-info="item" :key="item.name"/>
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
      list: [],
      OpenKeys: [],
      SelectedKeys: []
    }
  },
  methods: {
    loadActionTree () {
      HRequest.get('/api/action_tree').then(
        (response) => {
          // 在其中查找到选中的 action
          let actionName = this.$route.params.name
          let e = getElementFromArray(response.data.data, 'target_object', actionName, 'name')
          let path = e[1].split('-')
          this.OpenKeys = path.slice(0, [path.length - 1])
          this.SelectedKeys = path.slice([path.length - 1])
          this.list = response.data.data
        }
      )
    }
  },
  mounted () {
    this.loadActionTree()
  }
}
</script>
