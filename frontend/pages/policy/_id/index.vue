<template>
  <a-layout>
    <a-card>
      <router-link :to="{ name: 'policy' }">
        <a-icon type="left" /> <span>Return to list</span>
      </router-link>
      <a-card title="Approval Flow" :style="{ marginTop: '16px' }">
        <a-steps :space="100">
          <a-step title="Start" style="margin-top:24px;margin-bottom:24px"></a-step>
          <a-step v-for="(node, index) in nodesInfo" :key="index" :title="node.name" :description="node.approvers"
            style="margin-top:24px;margin-bottom:24px"></a-step>
          <a-step title="End" style="margin-top:24px;margin-bottom:24px"></a-step>
        </a-steps>
        <a-form layout="inline">
          <div>
            <a-col :span="12" style="margin-bottom: 24px">
              <a-form-item label="Flow Name">
                <a-input v-model="policyInfo.name" placeholder="input approver flow name" style="width:300px"></a-input>
              </a-form-item>
            </a-col>
            <a-col :span="12" style="margin-bottom: 24px">
              <a-form-item label="Description">
                <a-input v-model="policyInfo.display" placeholder="input description" style="width:300px"></a-input>
              </a-form-item>
            </a-col>
          </div>
        </a-form>

        <a-divider>Nodes</a-divider>

        <a-form v-for="(node, index) in nodesInfo" :key="index"
          style="margin-bottom: 24px" layout="inline" @change="changeInput">
          <a-form-item label="name" name="name">
            <a-input v-model="node.name" placeholder="input node name" :rules="{
              required: true,
              message: 'node name can not be null',
              trigger: 'change',
            }"></a-input>
          </a-form-item>
          <a-form-item label="approvers" name="approvers">
            <a-input v-model="node.approvers" placeholder="input node approvers"></a-input>
          </a-form-item>
          <a-form-item label="desc" name="desc">
            <a-input v-model="node.desc" placeholder="input node description"></a-input>
          </a-form-item>
          <a-form-item label="next" name="next">
            <a-input v-model="node.next" placeholder="input next node name"></a-input>
          </a-form-item>
          <a-form-item>
            <a-icon type="plus-circle" @click="addNode" />
          </a-form-item>
          <a-form-item v-if="index !== 0">
            <a-icon type="minus-circle" @click="removeNode(node)" />
          </a-form-item>
        </a-form>
        <div style="text-align: center; margin-top: 32px">
          <a-button type="primary" :disabled="!canSubmit" @click="handleSubmit">Submit</a-button>
        </div>
      </a-card>
    </a-card>
  </a-layout>
</template>

<script>
import { UTCtoLcocalTime } from '@/utils/HDate'
export default {
  data() {
    return {
      table_data: [{}],
      filtered: {},
      policyInfo: {},
      nodesInfo: [{}],
      loadingIntervalId: null,
      canSubmit: true,
      autoRefreshOn: false,
      autoRefreshDisabled: false,
      autoRefreshBtnText: 'Auto Refresh OFF',
      autoRefreshBtnUpdateTimer: null,
      isRefreshing: false,
    }
  },
  computed: {
  },
  watch: {
    '$route'() {
      this.loadPolicy()
    }
  },
  mounted() {
    this.loadPolicy()
  },
  methods: {
    UTCtoLcocalTime,
    loadPolicy () {
      this.$axios.get('/api/policies/' + this.$route.params.id).then(
        (response) => {
          this.table_data = response.data.policies
          if (this.table_data[0]) {
            this.policyInfo = this.table_data[0]
          }
          if (this.table_data[0?.definition?.nodes])  {
              this.nodesInfo = this.policyInfo.definition.nodes
          }
        })
    },
    addNode() {
      this.nodesInfo.push({})
    },
    removeNode(node) {
      const index = this.nodesInfo.indexOf(node);
      if (index !== -1) {
        this.nodesInfo.splice(index, 1);
      }
    },
    changeInput() {
      this.$forceUpdate()
    },
    handleSubmit() {
      const data = { "name": this.policyInfo.name, "display": this.policyInfo.display, "definition": { nodes: this.nodesInfo } }
      this.$axios.post('/api/policies/' + this.$route.params.id, data).then(
        (response) => {
          this.table_data = response.data.policies
          this.$message.success("submit success!")
        }).catch((e) => {
          this.$message.warning(JSON.stringify(e))
        })
      this.loadPolicy()
    }
  }
}
</script>

<style scoped>
.whiteBackground {
  background: #fff
}
</style>
