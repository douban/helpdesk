<template>
    <a-layout-content>
        <div style="margin-top:16px;margin-bottom:16px">
            <NuxtLink :to="{name: 'policy-id', params: {id: 0}}">
                <a-button type="primary">Create</a-button>
            </NuxtLink>
            <a-divider type="vertical" />
            <a-modal v-model="groupModalVisible" title="User Group" :footer="null" width="720px">
            <a-button type="primary" style="margin-bottom:16px" @click="addGroup">add</a-button>
            <a-table 
                size="small" 
                :pagination="false" 
                :columns="usersColumns" 
                :data-source="userGroup" 
                row-key="id"
                bordered>
                <span slot="action" slot-scope="text, record">
                <a-button v-if="record.id" type="link">edit</a-button>
                <a-popconfirm title="Sure to delete?" ok-text="Ok" cancel-text="Cancel" @confirm="delUserGroup(record.id)">
                    <a v-if="record.id">delete</a>
                </a-popconfirm>
                <a-button v-if="!record.id" type="link">save</a-button>
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
            filtered: {},
            loading: false,
            pagination: {
                pageSize: 1
            },
            userGroup: [],
            groupModalVisible: false,
            usersColumns: [{
                title: 'ID',
                key: 'id',
                dataIndex: 'id',
                width: 50,
            }, {
                title: 'Group',
                key: 'group_name',
                dataIndex: 'group_name',
            }, {
                title: 'Users',
                key: 'user_str',
                dataIndex: 'user_str',
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
        addGroup() {
            this.userGroup.push({})
        },
        addUserGroup() {

        },
        updateUserGroup(id) {
            const data = { "group_name": this.policyInfo.name, "user_str": this.policyInfo.display};
            this.$axios.put("/api/group_users/" + id, data).then(res => {
                this.$message.info("success!");
            }).catch((error) => {
                this.$message.warning(error);
            });
            this.loadUserGroup();
        },
        delUserGroup(id) {
            this.$axios.delete("/api/group_users/" + id).then(res => {
                this.$message.info("success!");
            }).catch((error) => {
                this.$message.warning(error);
            });
            this.loadUserGroup();
        }
    }, 
}
</script>

<style scoped>
.whiteBackground {
  background: #fff
}
</style>
