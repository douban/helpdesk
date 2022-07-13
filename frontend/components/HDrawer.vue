<template>
  <div>
    <a-drawer key="h-drawer" title="Admin Panel" :width="720" placement="right" :closable="false" :visible="visible"
      @close="onClose">
      <div slot="handle" class="ant-pro-setting-drawer-handle" @click="showDrawer">
        <a-icon type="setting" :style="{ color: '#fff', fontSize: '20px' }" />
      </div>

      <a-form v-for="(associate, index) in associates" :key="index" method="POST" layout="inline" hide-required-mark
        @submit="(e) => onSubmit(e, index)">
        <a-row>
          <a-form-item label="Approval Flow">
            <!-- <a-input v-model="associate.policy_id" name="policy_id" placeholder="Untitled" required="true"
              style="width: 240px" autocomplete="off"></a-input> -->
            <a-select v-model="associate.policy_id" :show-search="true" placeholder="select a approval flow" style="width: 240px" @search="handleSearch" @change="handleChange">
              <a-select-option v-for="item in policies" :key="item.id" :value="item.id">{{ item.name }}</a-select-option>
            </a-select>
          </a-form-item>
          <a-form-item v-if="associate.policy_id" label="Flow Detail">
          <a @click="gotoPolicyDetail(associate.policy_id)"> {{associate.policy_id}}</a>
          </a-form-item>        
        </a-row>
        <a-row>
          <a-form-item label="Rule">
            <a-textarea v-model="associate.link_condition" name="link_condition" rows="1"
              placeholder='e.g. ["onlycontains", ["split", "hosts", ","], "host1", "host2", "host3"]' required="true"
              style="width: 560px"></a-textarea>
          </a-form-item>
        </a-row>
        <a-row :style="{ textAlign: 'right' }">
        <a-form-item>
            <a-button type="danger" shape="circle" icon="close" :style="{ marginRight: '8px' }"
              :disabled="associate.length - 1 === index" @click="(e) => onDelete(e, index)" />
            <a-button html-type="submit" type="primary" shape="circle" icon="check" />
          </a-form-item>
        </a-row>
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
  data() {
    return {
      visible: false,
      handle: 'handle',
      associates: [{}],
      policies: [{}],
      currentPolicy: undefined,
      config_type: 'ticket',
    }
  },
  computed: {
    currentTicket() {
      return this.$route.params.action
    },
    url_associate() {
      return '/api/associates'
    },
  },
  watch: {
    '$route'() {
      // reload ActionDefinition when url changes
      this.clearStage()
    }
  },
  methods: {
    clearStage() {
      // clear stage , close the drawer
      this.associates = [{}]
      this.onClose()
    },
    showDrawer() {
      this.loadAssociates()
      this.loadPolicies()
      this.visible = !this.visible
    },
    loadAssociates() {
      this.$axios.get(this.url_associate, {params: {config_type: this.config_type, target_object: this.currentTicket}}).then(
        (response) => {
          if (response.status === 200 && response.data) {
            this.associates = response.data
          }
          this.associates.push({})
        }
      )
    },
    loadPolicies() {
      this.$axios.get("/api/policies").then((response) => {
        this.policies = response.data.items;
      });
    },
    handleSearch(value){
      this.handleChange(value)
    },
    handleChange(value){
      this.currentPolicy = (value !== null && value !== '') ? value : undefined
      },
    onClose() {
      this.visible = false
    },
    gotoPolicyDetail(id) {
      this.$router.push({path:'/policy/' + id})
    },
    onSubmit(e, index) {
      e.preventDefault()
      const data = { ticket_name: this.currentTicket, policy_id: this.associates[index].policy_id, link_condition: this.associates[index].link_condition }
      if (this.associates[index].id) {
        this.$axios.put('/api/associates/'+this.associates[index].id, data).then((response) => {
        if (response.data && response.data.id) {
          this.associates[index].id = response.data.id
        this.$message.success(JSON.stringify(response.data))
        if (this.associates.length - 1 === index) {
          this.associates.push({})
        }}
      }).catch((e) => {
        this.$message.warning(JSON.stringify(e))
      })
      } else {
        this.$axios.post(this.url_associate, data).then((response) => {
        if (response.data && response.data.id) {
          this.associates[index].id = response.data.id
        this.$message.success(JSON.stringify(response.data))
        if (this.associates.length - 1 === index) {
          this.associates.push({})
        }}
      }).catch((e) => {
        this.$message.warning(JSON.stringify(e))
      })
      }

    },
    onDelete(e, index) {
      e.preventDefault()
      this.$axios.delete('/api/associates/' + this.associates[index].id ).then((response) => {
        this.$message.success(JSON.stringify("delete success!"))
        this.associates.splice(index, 1)
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
