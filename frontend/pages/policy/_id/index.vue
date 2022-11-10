<template>
  <a-layout>
    <a-card class="cardCenter">
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
        <draggable  v-model="nodesInfo">
        <a-form v-for="(node, index) in nodesInfo" :key="index"
          style="margin-bottom: 24px" layout="inline" @change="changeInput">
          <a-form-item label="name" name="name">
            <a-input v-model="node.name" placeholder="input node name"></a-input>
          </a-form-item>
          <a-form-item label="node_type" name="node_type">
            <a-select v-model="node.node_type" allow-clear placeholder="select a node type" style="width: 160px">
              <a-select-option v-for="item in nodeType" :key="item.value" :value="item.value" >{{ item.name }}</a-select-option>
            </a-select>
          </a-form-item>
          <a-form-item label="approvers" name="approvers">
            <!-- <a-input v-model="node.approvers" placeholder="input node approvers"></a-input> -->
            <a-auto-complete
            v-model="node.approvers"
            :data-source="approverTips" 
            style="width: 200px"
            placeholder="input here"
            :filter-option="filterOption"/>
          </a-form-item>
          <a-form-item label="approver_type" name="approver_type">
            <a-select v-model="node.approver_type" allow-clear placeholder="select a approver type" style="width: 160px">
              <a-select-option v-for="item in approverType" :key="item.value" :value="item.value" >{{ item.name }}</a-select-option>
            </a-select>
          </a-form-item>
          <a-form-item>
            <a-icon type="plus-circle" @click="addNode" />
          </a-form-item>
          <a-form-item v-if="index !== 0">
            <a-icon type="minus-circle" @click="removeNode(node)" />
          </a-form-item>
        </a-form>
        </draggable>
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
import draggable from 'vuedraggable'
import HAssociateDrawer from '../../../components/HAssociateDrawer.vue'
import { UTCtoLcocalTime } from '@/utils/HDate'
export default {
    components: { 
      HAssociateDrawer,
      draggable, 
      },
    data() {
        return {
            filtered: {},
            policyInfo: {},
            nodesInfo: [{name:'', approvers: '', approver_type: '', node_type: ''}],
            loadingIntervalId: null,
            canSubmit: true,
            autoRefreshOn: false,
            autoRefreshDisabled: false,
            autoRefreshBtnText: "Auto Refresh OFF",
            autoRefreshBtnUpdateTimer: null,
            isRefreshing: false,
            showCreateOK: false,
            newPolicyId: 0,
            nodeType: [
              {"name": "抄送", "value": "cc"},
              {"name": "审批", "value": "approval"}
            ],
            approverType: [
              {"name": "指定人", "value": "people"},
              {"name": "用户组", "value": "group"},
              {"name": "dae应用owner", "value": "app_owner"},
              {"name": "部门负责人", "value": "department"},
            ],
            approverTips: []
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
        this.loadUserGroup();
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
            this.nodesInfo.push({name:'', approvers: '', approver_type: '', node_type: ''});
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
          this.showCreateOK = false
        },
        loadUserGroup() {
            this.$axios.get("/api/group_users").then((response) => {
                const groups = response.data
                groups.forEach(element => {
                  this.approverTips.push({ value: element.group_name, text: element.group_name})
                });
            });
            console.log(this.approverTips)
        },
        filterOption(input, option) {
          return option.componentOptions.children[0].text.toUpperCase().includes(input.toUpperCase()) >= 0
        }
    },
}
</script>

<style scoped>
.whiteBackground {
  background: #fff
}
.cardCenter {
 margin: auto;
 flex: auto;
 width: 1240px;
}
</style>
