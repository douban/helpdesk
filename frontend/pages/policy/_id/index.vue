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
          <a-form-item>
            <a-icon type="plus-circle" @click="addNode" />
          </a-form-item>
          <a-form-item v-if="index !== 0">
            <a-icon type="minus-circle" @click="removeNode(node)" />
          </a-form-item>
        </a-form>
        <div style="text-align: center; margin-top: 32px">
          <a-button type="primary" :disabled="!canSubmit" @click="handleSubmit">Submit</a-button>
            <a-modal
              v-model="showCreateOK"
              title="Submit success!"
              ok-text="Go detail"
              @ok="gotoNewPolicy"
              @cancel="showCreateOK = false"
            >
            <p>create approval flow success, id: {{ newPolicyId }}</p>
            </a-modal>
        </div>
      </a-card>
    </a-card>
    <h-associate-drawer></h-associate-drawer>
  </a-layout>
</template>

<script>
import HAssociateDrawer from '../../../components/HAssociateDrawer.vue'
import { UTCtoLcocalTime } from '@/utils/HDate'
export default {
    components: { HAssociateDrawer },
    data() {
        return {
            filtered: {},
            policyInfo: {},
            nodesInfo: [{name:'', approvers: '', desc: '', next: ''}],
            loadingIntervalId: null,
            canSubmit: true,
            autoRefreshOn: false,
            autoRefreshDisabled: false,
            autoRefreshBtnText: "Auto Refresh OFF",
            autoRefreshBtnUpdateTimer: null,
            isRefreshing: false,
            showCreateOK: false,
            newPolicyId: 0
        };
    },
    computed: {},
    watch: {
        "$route"() {
            this.loadPolicy();
        }
    },
    mounted() {
        this.loadPolicy();
    },
    methods: {
        UTCtoLcocalTime,
        loadPolicy() {
          if (this.$route.params.id !== 0) {
            this.$axios.get("/api/policies/" + this.$route.params.id).then((response) => {
              this.policyInfo = response.data;
              if (this.policyInfo.definition && this.policyInfo.definition.nodes) {
                this.nodesInfo = this.policyInfo.definition.nodes;
                }
            });
          }
        },
        addNode() {
            this.nodesInfo.push({name:'', approvers: '', desc: '', next: ''});
        },
        removeNode(node) {
            const index = this.nodesInfo.indexOf(node);
            if (index !== -1) {
                this.nodesInfo.splice(index, 1);
            }
        },
        changeInput() {
            this.$forceUpdate();
        },
        handleSubmit() {
          const data = { "name": this.policyInfo.name, "display": this.policyInfo.display, "definition": { nodes: this.nodesInfo } };
          if (this.$route.params.id === 0) {
            this.$axios.post("/api/policies", data).then((response) => {
                this.newPolicyId = response.data.id;
                this.$message.success("submit success!");
                this.showCreateOK = true
            }).catch((e) => {
                this.$message.warning(JSON.stringify(e));
            });
          } else {
            this.$axios.put("/api/policies/" + this.$route.params.id, data).then((response) => {
                this.policyInfo = response.data;
                this.$message.success("submit success!");
            }).catch((e) => {
                this.$message.warning(JSON.stringify(e));
            });
          }
          this.loadPolicy();
        },
        gotoNewPolicy () {
          this.$router.push({path:'/policy/' + this.newPolicyId})
        },
    },
}
</script>

<style scoped>
.whiteBackground {
  background: #fff
}
</style>
