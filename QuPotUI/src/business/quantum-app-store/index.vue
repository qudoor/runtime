<template>
  <layout-content :header="'选择云原生集群'">
    <complex-table ref="clusterData" local-key="cluster_columns" :row-key="getRowKeys" :selects.sync="clusterSelection"
      @selection-change="selectChange" :search-config="searchConfig" :data="data" :pagination-config="paginationConfig"
      @search="search" v-loading="loading">

      <el-table-column type="selection" :reserve-selection="true" fix></el-table-column>
      <el-table-column sortable :label="$t('commons.table.name')" min-width="100" prop="name" fix>
        <template v-slot:default="{ row }">
          <el-link v-if="row.status === 'Running'" type="info" @click="goForDetail(row)">{{ row.name }}</el-link>
          <span v-if="row.status !== 'Running'">{{ row.name }}</span>
        </template>
      </el-table-column>
      <!-- <el-table-column sortable :label="$t('cluster.project')" v-if="isAdmin" min-width="100" prop="projectName" fix /> -->
      <el-table-column sortable :label="$t('cluster.version')" min-width="75" prop="version" fix />
      <el-table-column sortable :label="$t('cluster.node_size')" min-width="70" prop="nodeSize" />

      <!-- <el-table-column label="GPU" min-width="70" prop="spec.supportGpu">
        <template v-slot:default="{ row }">
          <div v-if="row.status !== 'Running'">
            <span>{{ $t("commons.status." + row.spec.supportGpu.toLowerCase()) }}</span>
          </div>
          <div v-else>
            <div v-if="row.spec.supportGpu === 'enable' || row.spec.supportGpu === 'disable'">
              <el-link type="info" @click="onOpenGpuDialog(row)">{{ $t("commons.status." + row.spec.supportGpu) }}</el-link>
              <span>{{ $t("commons.status." + row.spec.supportGpu) }}</span>
            </div>
            <div v-if="row.spec.supportGpu === 'Creating'">
              <i class="el-icon-loading" />&nbsp; &nbsp; &nbsp;
              <el-link type="info" @click="openXterm(row)"> {{ $t("commons.status.creating") }}</el-link>
            </div>
            <div v-if="row.spec.supportGpu === 'Terminating'">
              <i class="el-icon-loading" />&nbsp; &nbsp; &nbsp;
              <el-link type="info" @click="openXterm(row)"> {{ $t("commons.status.terminating") }}</el-link>
            </div>
            <div v-if="row.spec.supportGpu === 'Waiting'">
              <i class="el-icon-loading" />{{ $t("commons.status.waiting") }}
            </div>
            <div v-if="row.spec.supportGpu === 'NotReady'">
              <span class="iconfont iconerror" style="color: #FA4147"></span> &nbsp; &nbsp; &nbsp;
              <el-link type="info" @click="getGpuStatus(row)">{{ $t("commons.status.not_ready") }}</el-link>
            </div>
            <div v-if="row.spec.supportGpu === 'Failed'">
              <span class="iconfont iconerror" style="color: #FA4147"></span> &nbsp; &nbsp; &nbsp;
              <el-link type="info" @click="getGpuStatus(row)">{{ $t("commons.status.failed") }}</el-link>
            </div>
          </div>
        </template>
      </el-table-column> -->

      <el-table-column :label="$t('commons.table.status')" min-width="100" prop="status">
        <template v-slot:default="{ row }">
          <div v-if="row.status === 'Running'">
            <span class="iconfont iconduihao" style="color: #32B350"></span>
            {{ $t("commons.status.running") }}
          </div>
          <div v-if="row.status === 'Failed'">
            <span class="iconfont iconerror" style="color: #FA4147"></span>
            {{ $t("commons.status.failed") }}
          </div>
          <div v-if="row.status === 'Initializing'">
            <i class="el-icon-loading" />
            {{ $t("commons.status.initializing") }}
          </div>
          <div v-if="row.status === 'Upgrading'">
            <i class="el-icon-loading" /> &nbsp; &nbsp; &nbsp;
            {{ $t("commons.status.upgrading") }}
          </div>
          <div v-if="row.status === 'Terminating' && row.provider === 'bareMetal'">
            <i class="el-icon-loading" /> &nbsp; &nbsp; &nbsp;
            {{ $t("commons.status.terminating") }}
          </div>
          <div v-if="row.status === 'Terminating' && row.provider !== 'bareMetal'">
            <i class="el-icon-loading" /> &nbsp; &nbsp; &nbsp;
            <span>{{ $t("commons.status.terminating") }} </span>
          </div>
          <div v-if="row.status === 'Creating'">
            <i class="el-icon-loading" />{{ $t("commons.status.creating") }}
          </div>
          <div v-if="row.status === 'Waiting'">
            <i class="el-icon-loading" />{{ $t("commons.status.waiting") }}
          </div>
          <div v-if="row.status === 'NotReady'">
            <span class="iconfont iconerror" style="color: #FA4147"></span> &nbsp; &nbsp; &nbsp;
            {{ $t("commons.status.not_ready") }}
          </div>
        </template>
      </el-table-column>
      <el-table-column width="140px" sortable :label="$t('commons.table.create_time')" prop="createdAt">
        <template v-slot:default="{ row }">
          {{ row.createdAt | datetimeFormat }}
        </template>
      </el-table-column>
    </complex-table>

  </layout-content>
</template>

<script>
import LayoutContent from "@/components/layout/LayoutContent"
import ComplexTable from "@/components/complex-table"
import {
  // healthCheck,
  // clusterRecover,
  searchClusters,
} from "@/api/cluster"
// import KoLogs from "@/components/ko-logs/index.vue"
import { checkPermission } from "@/utils/permisstion"

export default {
  name: "ClusterList",
  components: { ComplexTable, LayoutContent },
  data() {
    return {
      isAdmin: checkPermission("ADMIN"),
      paginationConfig: {
        currentPage: 1,
        pageSize: 10,
        total: 0,
      },
      clusterName: "",
      currentCluster: {
        spec: {},
      },
      clusterSelection: [],
      data: [],

      // cluster health check
      dialogCheckVisible: false,
      checkLoading: true,
      isRecover: false,
      recoverItems: [],
      checkData: {},

      gpuErrorInfo: "",

      // cluster logs
      dialogLogVisible: false,
      operationType: "",
      isRefresh: false,

      // cluster delete
      isForce: false,
      isUninstall: false,
      KoExternalNames: "",
      hasOnlyExternal: true,
      isKoExternalShow: false,
      dialogDeleteVisible: false,
      isDeleteButtonDisable: false,
      deleteName: "",

      searchConfig: {
        quickPlaceholder: this.$t("commons.search.quickSearch"),
        components: [
          { field: "name", label: this.$t("commons.table.name"), component: "FuComplexInput", defaultOperator: "eq" },
          {
            field: "created_at",
            label: this.$t("commons.table.create_time"),
            component: "FuComplexDate",
            valueFormat: "yyyy-MM-dd"
          },
        ],
      },
      loading: false,
      timer: null,
    }
  },
  methods: {
    getRowKeys(row) {
      return row.name
    },
    search(condition) {
      this.loading = true
      this.$refs.clusterData?.clearSelection()
      const { currentPage, pageSize } = this.paginationConfig
      searchClusters(currentPage, pageSize, condition, false).then((data) => {
        this.loading = false
        this.data = data.items || []
        this.paginationConfig.total = data.total
      })
    },
    searchForPolling(condition) {
      const { currentPage, pageSize } = this.paginationConfig
      searchClusters(currentPage, pageSize, condition, true).then((data) => {
        this.data = data.items || []
        this.paginationConfig.total = data.total
      })
    },
    goForDetail(row) {
      this.$router.push({ name: "StoreQuantumAppList", params: { project: row.projectName, cluster: row.name } })
    },
    selectChange() {
      let isOk = true
      if (this.clusterSelection.length === 0) {
        this.isDeleteButtonDisable = true
        return
      }
      for (const item of this.clusterSelection) {
        if (item.status !== "Running" && item.status !== "Failed" && item.status !== "NotReady") {
          isOk = false
          break
        }
      }
      this.isDeleteButtonDisable = !isOk
    },
    // // cluster health check
    // onHealthCheck(row) {
    //   this.checkData = {}
    //   if (!row) {
    //     row = this.clusterSelection[0]
    //   }
    //   this.currentCluster = row
    //   this.dialogCheckVisible = true
    //   this.checkLoading = true
    //   this.isRecover = false
    //   healthCheck(this.currentCluster.name).then((data) => {
    //     this.checkData = data
    //     this.checkLoading = false
    //   })
    // },
    // onRecover() {
    //   this.recoverItems = []
    //   this.checkLoading = true
    //   this.isRecover = true
    //   clusterRecover(this.currentCluster.name, this.checkData).then((data) => {
    //     this.checkData = { hooks: [], level: "" }
    //     this.recoverItems = data
    //     this.checkLoading = false
    //   })
    // },

    // getStatus(row) {
    //   this.isRefresh = !this.isRefresh
    //   this.operationType = (row.status.indexOf("NotReady") !== -1) ? "not-ready" : "create-cluster"
    //   this.dialogLogVisible = true
    //   this.clusterName = row.name
    // },

    polling() {
      this.timer = setInterval(() => {
        let flag = false
        const needPolling = ["Initializing", "Terminating", "Creating", "Waiting", "Upgrading"]
        for (const item of this.data) {
          // if (needPolling.indexOf(item.status) !== -1 || needPolling.indexOf(item.spec.supportGpu) !== -1) {
          if (needPolling.indexOf(item.status) !== -1) {
            flag = true
            break
          }
        }
        if (flag) {
          this.searchForPolling()
        }
      }, 10000)
    },
  },
  mounted() {
    this.search()
    this.polling()
  },
  destroyed() {
    clearInterval(this.timer)
    this.timer = null
  },
}
</script>

<style lang="scss" scoped>
.dialog {
  ::v-deep .el-scrollbar__wrap {
    height: 100%;
    overflow-x: hidden;
  }
}
</style>
