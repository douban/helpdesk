<template>
  <div>
    <div style="margin: 10px">
      <a-input-search v-model="searchText" style="margin-bottom: 8px" placeholder="Search" />
    </div>
    <a-menu
      v-model="SelectedKeys"
      :open-keys.sync="openKeys"
      mode="inline"
      :style="{ height: '100%', borderRight: 0, 'background-color': 'white'}"
      @openChange="onOpenChange"
    >
      <template v-for="item in list">
        <!-- 如果要更改此处的自定义渲染, 请同时修改下方 import 的 SubMenu 内的渲染, 以保证一致 -->
        <a-menu-item v-if="!item.children" :key="item.name">
          <router-link v-if="item.target_object"
            :to="{ name: 'action', params: { name: item.target_object }}"
            :title="item.desc"
          >
            {{item.name}}
          </router-link>
          <span v-else>{{item.name}}</span>
        </a-menu-item>
        <sub-menu v-else :key="item.name" :menu-info="item"/>
      </template>
    </a-menu>
  </div>
</template>

<script>
import { addKeyForEachElement, getElementFromArray, getElementsContains } from '~/utils/HFinder'

export default {
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
  beforeMount () {
    this.loadActionTree()
  },
  methods: {
    loadActionTree () {
      this.$axios.get('/api/action_tree').then(
        (response) => {
          let definition = [{name: response.data[0].name}]
          definition.push.apply(definition, response.data[0].children)
          // add key for each element in tree
          definition = addKeyForEachElement(definition)
          for (let i = 0; i < definition.length; i++) {
            this.rootSubmenuKeys.push(definition[i].key)
          }
          this.checkActionTreeError(definition)
          this.$store.dispatch('updateActionTree', definition)
          const actionName = this.$route.params.action
          // looking for selected item with actionName
          const e = getElementFromArray(definition, 'target_object', actionName, 'key')
          if (e !== undefined) {
            const path = e.key.split('-')
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
      const loadErrorAction = []
      for (let i = 0; i < definition.length; i++) {
        if (definition[i].children && definition[i].children.length === 0) {
          loadErrorAction.push(definition[i].name)
        }
      }

      if (loadErrorAction.length > 0) {
        this.$notification.open({
          message: "Action tree load error",
          description: loadErrorAction.join(",") + " pack load error",
          duration: 0,
          icon: '<a-icon type="warning" style="color: red" />',
          key: this.actionLoadNotifyKey
        })
      }
    },
    onOpenChange (openKeys) {
      const latestOpenKey = openKeys.find(key => !this.openKeys.includes(key))
      if (!this.rootSubmenuKeys.includes(latestOpenKey)) {
        this.openKeys = openKeys
      } else {
        this.openKeys = latestOpenKey ? [latestOpenKey] : []
      }
    },
    // TODO: search menu
    onSearchChange (e) {
      console.log(e)
    }
  }
}

</script>
