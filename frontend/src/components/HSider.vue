<template>
  <div>
    <a-menu
      v-model="SelectedKeys"
      :openKeys="openKeys"
      mode="inline"
      :style="{ height: '100%', borderRight: 0 }"
      @openChange="onOpenChange"
    >
      <template v-for="item in list">
        <!-- 如果要更改此处的自定义渲染, 请同时修改下方 import 的 SubMenu 内的渲染, 以保证一致 -->
        <a-menu-item v-if="!item.children" :key="item.name">
          <router-link v-if="item.target_object"
            :to="{ name: 'FormView', params: { name: item.target_object }}"
            :title="item.desc"
          >
            {{item.name}}
          </router-link>
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
import {addKeyForEachElement, getElementFromArray} from '../utils/HFinder'

export default {
  components: {
    'sub-menu': SubMenu
  },
  data () {
    return {
      collapsed: false,
      openKeys: [],
      SelectedKeys: [],
      rootSubmenuKeys: []
    }
  },
  computed: {
    list () {
      return this.$store.state.actionTree
    },
    firstAction () {
      return this.$store.getters.firstAction
    }
  },
  methods: {
    loadActionTree () {
      HRequest.get('/api/action_tree').then(
        (response) => {
          let definition = [{name: '功能导航'}]
          definition.push.apply(definition, response.data.data[0].children)
          // add key for each element in tree
          definition = addKeyForEachElement(definition)
          for (let i = 0; i < definition.length; i++) {
            this.rootSubmenuKeys.push(definition[i].key)
          }
          this.$store.dispatch('updateActionTree', definition)
          let actionName = this.$route.params.name
          // looking for selected item with actionName
          let e = getElementFromArray(definition, 'target_object', actionName, 'key')
          if (e !== undefined) {
            let path = e.key.split('-')
            this.SelectedKeys = [e.key]
            this.openKeys = []
            for (let i = 1; i < path.length; i++) {
              this.openKeys.push(path.slice(0, i).join('-'))
            }
          }
        }
      )
    },
    onOpenChange (openKeys) {
      const latestOpenKey = openKeys.find(key => this.openKeys.indexOf(key) === -1)
      if (this.rootSubmenuKeys.indexOf(latestOpenKey) === -1) {
        this.openKeys = openKeys
      } else {
        this.openKeys = latestOpenKey ? [latestOpenKey] : []
      }
    },
    // TODO: search menu
    onSearchChange (e) {
    }
  },
  beforeMount () {
    this.loadActionTree()
  }
}

</script>
