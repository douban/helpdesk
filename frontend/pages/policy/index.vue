<template>
    <a-layout-content>
        <div style="margin-top:16px;margin-bottom:16px">
            <NuxtLink :to="{name: 'policy-id', params: {id: 0}}">
                <a-button type="primary">Create</a-button>
            </NuxtLink>
            <a-divider type="vertical" />
            <a-modal v-model="groupModalVisible" title="User Group" :footer="null" width="800px">
            <a-modal v-model="editVisible" title="Edit User Group" @ok="addUserGroup" @cancel="editVisible = false">
            <a-form :model="editUserGroup">
              <a-form-item label="Group Name">
                <a-input v-model="editUserGroup.group_name" placeholder="input group name"></a-input>
              </a-form-item>
              <a-form-item label="Users">
                <a-input v-model="editUserGroup.user_str" placeholder="input users" ></a-input>
              </a-form-item>
            </a-form>
            </a-modal>
                <a-button type="primary" style="margin-bottom:16px" @click="showEditModal({})">add</a-button>
                <a-table size="small" :pagination="false" :columns="usersColumns" :data-source="userGroup" row-key="id" :scroll="{ y: 360 }" bordered>
                    <span slot="action" slot-scope="text, record">
                        <a-button type="link" @click="showEditModal(record)">edit</a-button>
                        <a-popconfirm title="Sure to delete?" ok-text="Ok" cancel-text="Cancel"
                            @confirm="delUserGroup(record.id)">
                            <a>delete</a>
                        </a-popconfirm>
                    </span>
                </a-table>
            </a-modal>
            <a-button type="link" icon="team" @click="showGroupModal"> UserGroup </a-button>
        </div>
        <a-table 
            :columns="columns" 
            :data-source="tableData" 
            :pagination="pagination" 
            :loading="loading" 
            row-key="id"
            class="whiteBackground" 
            @change="handleTableChange">
            <span slot="action" slot-scope="text, record">
                <NuxtLink :to="{name: 'policy-id', params: {id: record.id}}">detail</NuxtLink>
                <a-divider type="vertical" />
                <a-popconfirm title="Sure to delete?" ok-text="Ok" cancel-text="Cancel" @confirm="delPolicy(record.id)">
                    <a>delete</a>
                </a-popconfirm>
            </span>
        </a-table>
    </a-layout-content>
</template>

<script>
import {cmp} from '@/utils/HComparer'
import {UTCtoLcocalTime} from '@/utils/HDate'

export default {
    name: "HPolicyList",
    data() {
        return {
            tableData: [],
            loading: false,
            pagination: {
                pageSize: 1
            },
            userGroup: [],
            editUserGroup: {id: 0, group_name: "", user_str: ""},
            groupModalVisible: false,
            editVisible: false,
            usersColumns: [{
                title: 'ID',
                key: 'id',
                dataIndex: 'id',
                width: 50,
            }, {
                title: 'Group',
                key: 'group_name',
                dataIndex: 'group_name',
                width: 100,
            }, {
                title: 'Users',
                key: 'user_str',
                dataIndex: 'user_str',
                width: 400,
            }, {
                title: 'Action',
                key: 'action',
                width: 150,
                scopedSlots: { customRender: "action" }
            }],
        };
    },
    computed: {
        columns() {
            return [{
                    title: "ID",
                    key: "id",
                    dataIndex: "id",
                    sorter: (a, b) => cmp(a, b, "id"),
                    scopedSlots: { customRender: "id" }
                }, {
                    title: "Name",
                    key: "name",
                    dataIndex: "name",
                    sorter: (a, b) => cmp(a, b, "name")
                }, {
                    title: "Display",
                    key: "display",
                    width: 150,
                    dataIndex: "display",
                    sorter: (a, b) => cmp(a, b, "display"),
                    scopedSlots: { customRender: "display" }
                }, {
                    title: "By",
                    key: "created_by",
                    dataIndex: "created_by",
                    sorter: (a, b) => cmp(a, b, "created_by")
                }, {
                    title: "Create Time",
                    key: "created_at",
                    dataIndex: "created_at",
                    sorter: (a, b) => cmp(a, b, "created_at"),
                    customRender: (text) => {
                        return UTCtoLcocalTime(text);
                    }
                }, {
                    title: "Update by",
                    key: "updated_by",
                    dataIndex: "updated_by",
                    sorter: (a, b) => cmp(a, b, "updated_by")
                }, {
                    title: "Update Time",
                    key: "updated_at",
                    dataIndex: "updated_at",
                    sorter: (a, b) => cmp(a, b, "updated_at"),
                    customRender: (text) => {
                        return UTCtoLcocalTime(text);
                    }
                }, {
                    title: "Action",
                    key: "action",
                    width: 230,
                    scopedSlots: { customRender: "action" }
                }];
        }
    },
    mounted() {
        const queryParams = this.$route.query;
        if (queryParams.page === undefined) {
            queryParams.page = 1;
        }
        if (queryParams.size === undefined) {
            queryParams.size = 10;
        }
        queryParams.page = Number(queryParams.page);
        queryParams.size = Number(queryParams.size || 10);
        this.loadPolicies(queryParams);
    },
    methods: {
        loadPolicies(params) {
            this.pagination.current = params.page;
            this.loading = true;
            this.$axios.get("/api/policies", { params }).then((response) => {
                this.handlePolicyList(response);
            });
        },
        handlePolicyList(response) {
            this.pagination.total = response.data.total;
            this.pagination.current = response.data.page;
            this.pagination.pageSize = response.data.size || 20;
            this.pagination = { ...this.pagination };
            this.tableData = response.data.items;
            this.loading = false;
        },
        handleTableChange (pagination, sorter) {
            const queryParams = {page: pagination.current, size: pagination.pageSize}
            if (sorter.columnKey !== undefined) {
                queryParams.order_by = sorter.columnKey
                if (sorter.order === 'ascend') {
                    queryParams.desc = false
                } else {
                    queryParams.desc = true
                }
            }
            this.loadPolicies(queryParams)
        },
        delPolicy(id) {
            this.$axios.delete("/api/policies/" + id).then(res => {
                this.$message.info("success!");
            }).catch((error) => {
                this.$message.warning(error);
            });
            this.loadPolicies(this.$route.params);
        },
        loadUserGroup() {
            this.$axios.get("/api/group_users").then((response) => {
                this.userGroup = response.data
            });
        },
        showGroupModal() {
            this.loadUserGroup()
            this.groupModalVisible = true
        },
        showEditModal (record) {
            if (record) {
                this.editUserGroup = record
            }
            this.editVisible = true
            this.groupModalVisible = false
        },
        addUserGroup() {
            const data = {"group_name": this.editUserGroup.group_name, "user_str": this.editUserGroup.user_str}
            if (this.editUserGroup.id) {
                this.$axios.put("/api/group_users/" + this.editUserGroup.id, data).then((response) => {
                this.$message.success("submit success!");
                this.editVisible = false
            }).catch((e) => {
                this.$message.warning(JSON.stringify(e));
            })
            } else {
                this.$axios.post("/api/group_users", data).then((response) => {
                this.$message.success("submit success!");
                this.editVisible = false
            }).catch((e) => {
                this.$message.warning(JSON.stringify(e));
            })
            }
        },
        delUserGroup(id) {
            this.$axios.delete("/api/group_users/" + id).then(res => {
                this.$message.info("success!");
            }).catch((error) => {
                this.$message.warning(error);
            });
            this.groupModalVisible = false
        }
    }, 
}
</script>

<style scoped>
.whiteBackground {
  background: #fff
}
</style>
