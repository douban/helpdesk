<template>
  <div>
    <a-drawer
      key="h-drawer"
      title="Admin Panel"
      :width="720"
      placement="right"
      :closable="false"
      :visible="visible"
      @close="onClose"
    >
      <div slot="handle" class="ant-pro-setting-drawer-handle" @click="showDrawer">
        <a-icon type="setting" :style="{color: '#fff', fontSize: '20px'}"/>
      </div>

      <a-form v-for="(paramRule, index) in paramRules"
              :key="index"
              method="POST"
              layout="vertical"
              hide-required-mark
              @submit="(e) => onSubmit(e, index)"
      >
        <a-row :gutter="16">
          <a-col>
            <a-form-item label="Title">
              <a-input v-model="paramRule.title" name="title"
                       placeholder="Untitled"
              ></a-input>
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col>
            <a-form-item label="Rule">
              <a-textarea v-model="paramRule.rule"
                          name="rule"
                          rows="1"
                          placeholder='e.g. ["onlycontains", ["split", "hosts", ","], "host1", "host2", "host3"]'
                          autosize
                          required="true"
              ></a-textarea>
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="6">
            <a-form-item label="Is auto-approval?">
              <a-checkbox name="is_auto_approval"
                          :checked="paramRule.is_auto_approval"
                          @change="(e) => onCheckboxChange(e, index, 'is_auto_approval')"
              ></a-checkbox>
            </a-form-item>
          </a-col>
          <a-col :span="18">
            <a-form-item label="Approver">
              <a-input v-model="paramRule.approver" name="approver"
                       placeholder="Approver names seperated by comma"
              ></a-input>
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item :style="{textAlign: 'right'}"
        >
          <a-button type="danger" shape="circle" icon="close"
                    :style="{marginRight: '8px'}"
                    :disabled="paramRules.length - 1 === index"
                    @click="(e) => onDelete(e, index)"
          />
          <a-button html-type="submit" type="primary" shape="circle" icon="check" />
        </a-form-item>

        <a-divider />
      </a-form>

      <div>
        <a-collapse accordion :bordered="false">
          <a-collapse-panel key="1" header="Debug Info">
            <div>
              <p>{{ actionDefinition }}</p>
            </div>
          </a-collapse-panel>
        </a-collapse>
      </div>

    </a-drawer>
  </div>
</template>

<script>
export default {
  name: 'HDrawer',
  props: ['actionDefinition'],
  data () {
    return {
      visible: false,
      handle: 'handle',
      paramRules: null
    }
  },
  computed: {
    currentForm () {
      return this.$route.params.name
    },
    url_param_rule () {
      return '/api/admin_panel/' + this.currentForm + '/param_rule'
    },
    url_param_rule_add () {
      return '/api/admin_panel/' + this.currentForm + '/param_rule/add'
    },
    url_param_rule_del () {
      return '/api/admin_panel/' + this.currentForm + '/param_rule/del'
    }
  },
  watch: {
    '$route' () {
      // reload ActionDefinition when url changes
      this.clearStage()
    }
  },
  methods: {
    clearStage () {
      // clear stage , close the drawer
      this.paramRules = null
      this.onClose()
    },
    showDrawer () {
      this.loadParamRules()
      this.visible = !this.visible
    },
    loadParamRules () {
      if (this.paramRules) {
        return
      }
      this.paramRules = [{}]
      this.$axios.get(this.url_param_rule).then(
        (response) => {
          if (response.status === 200 && response.data) {
            if (response.data !== []) {
              this.paramRules = response.data
            }
          }
          this.paramRules.push({})
        }
      )
    },
    onClose () {
      this.visible = false
    },
    onCheckboxChange (e, index, attr) {
      const paramRule = this.paramRules[index]
      paramRule[attr] = e.target.checked
      this.paramRules.splice(index, 1, paramRule)
    },
    onSubmit (e, index) {
      e.preventDefault()
      this.$axios.post(this.url_param_rule_add, this.paramRules[index]).then((response) => {
        if (response.data && response.data.id) {
          this.paramRules[index].id = response.data.id
        }
        this.$message.success(JSON.stringify(response.data))
        if (this.paramRules.length - 1 === index) {
          this.paramRules.push({})
        }
      }).catch((e) => {
        this.$message.warning(JSON.stringify(e))
      })
    },
    onDelete (e, index) {
      e.preventDefault()
      this.$axios.post(this.url_param_rule_del, this.paramRules[index]).then((response) => {
        this.$message.success(JSON.stringify(response.data))
        // delete in js
        this.paramRules.splice(index, 1)
      })
    }

  }
}
</script>

<style scoped>
.ant-pro-setting-drawer-handle {
  position: absolute;
  top: 240px;
  right: 720px;
  z-index: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  font-size: 16px;
  text-align: center;
  background: #1890ff;
  border-radius: 4px 0 0 4px;
  cursor: pointer;
  pointer-events: auto;
}
</style>
