<template>
  <layout-content :header="$t('user.user')">
    <complex-table :data="data" local-key="user_columns" :pagination-config="paginationConfig" @search="search"
      v-loading="loading" :selects.sync="selects" :fit="true">
      <template #toolbar>
        <el-button-group>
          <el-button size="small" @click="create()">{{ $t("commons.button.create") }}</el-button>
          <el-button size="small" :disabled="selects.length === 0" @click="del()">{{ $t("commons.button.delete") }}
          </el-button>
        </el-button-group>
      </template>
      <el-table-column type="selection" fix></el-table-column>
      <el-table-column sortable :label="$t('commons.table.name')" prop="username" mix-width="120">
        <template v-slot:default="{ row }">
          <el-row>
            <el-col :span="18">
              {{ row.username }}<br />
            </el-col>
          </el-row>
        </template>
      </el-table-column>
      <el-table-column sortable :label="$t('user.email')" prop="email" min-width="120">
        <template v-slot:default="{ row }">
          <el-row>
            <el-col>
              {{ row.email }}
            </el-col>
          </el-row>
        </template>
      </el-table-column>
      <!-- <el-table-column :label="$t('commons.table.status')">
        <template v-slot:default="{row}">
          <el-switch :disabled="currentUser.username === row.username || row.username === 'admin'" @change="changeStatus(row)" v-model="row.status" active-value="active" inactive-value="passive" />
        </template>
      </el-table-column> -->
      <!-- <el-table-column :label="$t('user.type')">
        <template v-slot:default="{row}">
          <span v-if="row.type === 'LDAP'">{{ $t("user.ldap") }}</span>
          <span v-if="row.type === 'LOCAL'">{{ $t("user.local") }}</span>
        </template>
      </el-table-column> -->
      <!-- <el-table-column :label="$t('user.role')" min-width="80">
        <template v-slot:default="{row}">
          <span size="small">{{ $t(`commons.role.${row.role}`) }}</span>
        </template>
      </el-table-column> -->
      <el-table-column sortable :label="$t('commons.table.create_time')" prop="createdAt" min-width="100">
        <template v-slot:default="{ row }">
          {{ row.createdAt | datetimeFormat }}
        </template>
      </el-table-column>
      <fu-table-operations :buttons="buttons" :label="$t('commons.table.action')" fix />
    </complex-table>
  </layout-content>
</template>

<script>
import LayoutContent from "@/components/layout/LayoutContent"
import { listUsers, deleteUser, updateUser } from "@/api/user"
import ComplexTable from "@/components/complex-table"
import { getCurrentUser } from "@/api/user-token"


export default {
  name: "UserList",
  components: { ComplexTable, LayoutContent },
  data() {
    return {
      buttons: [
        {
          label: this.$t("commons.button.edit"), icon: "el-icon-edit", click: (row) => {
            this.$router.push({ name: "UserEdit", params: { username: row.username } })
          }, disabled: (row) => {
            return row.type === "LDAP"
          }
        },
        {
          label: this.$t("commons.button.delete"), icon: "el-icon-delete", click: (row) => {
            this.del(row.username)
          }, disabled: (row) => {
            return this.currentUser.username === row.username || row.username === "admin"
          }
        },
      ],
      paginationConfig: {
        currentPage: 1,
        pageSize: 10,
        total: 0,
      },
      data: [],
      loading: false,
      selects: [],
      currentUser: {}
    }
  },
  methods: {
    create() {
      this.$router.push({ name: "UserCreate" })
    },
    search(condition) {
      this.loading = true
      const { currentPage, pageSize } = this.paginationConfig
      listUsers(currentPage, pageSize, condition).then(data => {
        this.loading = false
        this.data = data.items
        this.paginationConfig.total = data.total
      })
    },
    del(name) {
      this.$confirm(this.$t("commons.confirm_message.delete"), this.$t("commons.message_box.prompt"), {
        confirmButtonText: this.$t("commons.button.confirm"),
        cancelButtonText: this.$t("commons.button.cancel"),
        type: "warning"
      }).then(() => {
        if (name) {
          deleteUser(name).then(() => {
            this.search()
            this.$message({
              type: "success",
              message: `${name}${this.$t("commons.msg.delete_success")}!`
            })
          })
        } else {
          const ps = []
          for (const item of this.selects) {
            ps.push(deleteUser(item.name))
          }
          Promise.all(ps).then(() => {
            this.search()
            this.$message({
              type: "success",
              message: this.$t("commons.msg.delete_success"),
            })
          })
        }
      })
    },
    changeStatus(row) {
      updateUser(row.username, row).then(() => {
        this.$message({
          type: "success",
          message: `${this.$t("commons.msg.save_success")}!`
        })
        this.search()
      })
    }
  },
  created() {
    getCurrentUser().then(res => {
      this.currentUser = res
      this.search()
    })
  },
}
</script>
<style scoped lang="scss"></style>
