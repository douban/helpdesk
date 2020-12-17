<template>
  <div>
    <div style="margin: 10px">
      <a-input-search style="margin-bottom: 8px" placeholder="Search" v-model="searchText" />
    </div>
    <a-menu
      v-model="SelectedKeys"
      :openKeys="openKeys"
      mode="inline"
      :style="{ height: '100%', borderRight: 0, 'background-color': 'white'}"
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
import {addKeyForEachElement, getElementFromArray, getElementsContains} from '../utils/HFinder'
import AInputSearch from 'ant-design-vue/es/input/Search'

export default {
  components: {
    AInputSearch,
    'sub-menu': SubMenu
  },
  data () {
    return {
      collapsed: false,
      openKeys: [],
      SelectedKeys: [],
      rootSubmenuKeys: [],
      searchText: '',
      actionLoadNotifyKey: 'actionTreeLoadErrorNofify'
    }
  },
  computed: {
    list () {
      if (!this.searchText) {
        return this.$store.state.actionTree
      }
      return getElementsContains(this.$store.state.actionTree, this.searchText)
    },
    firstAction () {
      return this.$store.getters.firstAction
    }
  },
  methods: {
    loadActionTree () {
      HRequest.get('/api/action_tree').then(
        (response) => {
          let definition = [{name: response.data.data[0].name}]
          definition.push.apply(definition, response.data.data[0].children)
          // add key for each element in tree
          definition = addKeyForEachElement(definition)
          for (let i = 0; i < definition.length; i++) {
            this.rootSubmenuKeys.push(definition[i].key)
          }
          this.checkActionTreeError(definition)
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
    checkActionTreeError(definition) {
      // check action 
      var loadErrorAction = []  
      for (let i = 0; i < definition.length; i++) {
        if (definition[i].children && definition[i].children.length == 0) {
          loadErrorAction.push(definition[i].name)
        }
      }

      if (loadErrorAction.length > 0) {
        this.$notification.open({
          message: "Action tree load error",
          description: loadErrorAction.join(",") + " pack load error",
          duration: 0,
          icon: <a-icon type="warning" style="color: red" />,
          key: this.actionLoadNotifyKey
        })
      }
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
      console.log(e)
    }
  },
  beforeMount () {
    this.loadActionTree()
  }
}

</script>
