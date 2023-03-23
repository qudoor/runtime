<template>
  <div>
    <el-alert v-if="provider === ''" :title="$t('cluster.detail.node.operator_help')" type="info" />
    <complex-table style="margin-top: 20px" ref="nodeData" :row-key="getRowKeys" :selects.sync="selects"
      @search="search" :data="data" v-loading="loading" :pagination-config="paginationConfig">
      <!-- <el-table-column type="selection" :reserve-selection="true" fix></el-table-column> -->
      <el-table-column sortable :label="$t('commons.table.name')" show-overflow-tooltip min-width="100" prop="name" fix>
        <template v-slot:default="{ row }">
          <el-link v-if="row.status.indexOf('Running') !== -1" type="info" @click="getDetailInfo(row)">{{
            row.name
          }}</el-link>
          <span v-if="row.status.indexOf('Running') === -1">{{ row.name }}</span>
        </template>
      </el-table-column>
      <el-table-column label="IP" width="120px" fix>
        <template v-slot:default="{ row }">{{ getInternalIp(row) }}</template>
      </el-table-column>
      <el-table-column label="Role" show-overflow-tooltip min-width="100" prop="role" fix />
      <el-table-column sortable class="ko-status" :label="$t('commons.table.status')" prop="status" fix>
        <template v-slot:default="{ row }">
          <div v-if="row.status.indexOf('Terminating') !== -1 && currentCluster.provider !== 'bareMetal'">
            <i class="el-icon-loading" />&nbsp; &nbsp; &nbsp;
            {{ $t("commons.status.terminating") }}
          </div>
          <div v-if="row.status.indexOf('Terminating') !== -1 && currentCluster.provider === 'bareMetal'">
            <i class="el-icon-loading" /> &nbsp; &nbsp; &nbsp;
            <el-link type="info" @click="getStatus(row)">{{ $t("commons.status.terminating") }} </el-link>
          </div>
          <div v-if="row.status === 'Failed'">
            <span class="iconfont iconerror" style="color: #FA4147"></span> &nbsp; &nbsp; &nbsp;
            <el-link type="info" @click="getStatus(row)">{{ $t("commons.status.failed") }}</el-link>
          </div>
          <div v-if="row.status === 'Lost'">
            <span class="iconfont iconerror" style="color: #FA4147"></span> &nbsp; &nbsp; &nbsp;
            {{ $t("commons.status.lost") }}
          </div>
          <div v-if="row.status === 'Initializing'">
            <i class="el-icon-loading" />&nbsp; &nbsp; &nbsp;
            <el-link type="info" @click="getStatus(row)"> {{ $t("commons.status.initializing") }}</el-link>
          </div>
          <div v-if="row.status.indexOf('Running') !== -1">
            <span class="iconfont iconduihao" style="color: #32B350"></span>
            {{ $t("commons.status.running") }}
          </div>
          <div v-if="row.status.indexOf('SchedulingDisabled') !== -1">
            <span class="iconfont icondiable" style="color: #FA4147"></span>
            {{ $t("commons.status.disable_scheduling") }}
          </div>
          <div v-if="row.status === 'Creating'">
            <i class="el-icon-loading" />&nbsp; &nbsp; &nbsp;
            {{ $t("commons.status.creating") }}
          </div>
          <div v-if="row.status === 'Waiting'">
            <i class="el-icon-loading" />&nbsp; &nbsp; &nbsp;
            <span>{{ $t("commons.status.waiting") }}</span>
          </div>

          <div v-if="row.status === 'NotReady'">
            <span class="iconfont iconping" style="color: #FA4147"></span>
            {{ $t("commons.status.not_ready") }}
          </div>
        </template>
      </el-table-column>
      <el-table-column sortable :label="$t('commons.table.create_time')" prop="createdAt">
        <template v-slot:default="{ row }">
          {{ row.createdAt | datetimeFormat }}
        </template>
      </el-table-column>

      <!-- <fu-table-operations :buttons="buttons" :label="$t('commons.table.action')" fix /> -->
    </complex-table>

    <el-dialog :title="$t('commons.button.create')" width="30%" :visible.sync="dialogCreateVisible">
      <el-form label-position='left' :model="createForm" ref="createForm" :rules="rules" label-width="110px">
        <el-form-item v-if="provider === 'plan'" prop="increase" :label="$t('cluster.detail.node.increment')">
          <el-input-number :max="maxNodeNum" style="width: 80%" v-model.number="createForm.increase" clearable />
          <div><span class="input-help">{{
            $t('cluster.detail.node.node_expand_help', [currentCluster.spec.maxNodeNum -
              data.length])
          }}</span></div>
        </el-form-item>

        <span v-if="provider === 'bareMetal'">{{ $t('cluster.creation.node_help') }}</span>
        <el-form-item v-if="provider === 'bareMetal'" prop="hosts" :label="$t('cluster.detail.node.host')"
          style="margin-top:20px">
          <el-select style="width: 80%" v-model="createForm.hosts" multiple clearable>
            <el-option v-for="item of hosts" :key="item.name" :value="item.name">{{ item.name }}({{
              item.ip
            }})</el-option>
          </el-select>
          <div><span class="input-help">{{ $t('cluster.detail.node.node_expand_help', [maxNodeNum]) }}</span></div>
        </el-form-item>
        <el-form-item v-if="supportGpu === 'disable' && !gpuExist" prop="supportGpu"
          :label="$t('cluster.creation.support_gpu')">
          <el-switch style="width: 80%" active-value="enable" inactive-value="disable"
            v-model="createForm.supportGpu" />
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogCreateVisible = false">{{ $t('commons.button.cancel') }}</el-button>
        <el-button type="primary" :disabled="provider === '' || submitLoading" @click="submitCreate()"
          v-preventReClick>{{ $t('commons.button.ok') }}</el-button>
      </div>
    </el-dialog>

    <el-dialog :title="$t('cluster.detail.node.node_detail')" width="50%" :visible.sync="dialogDetailVisible">
      <div class="dialog">
        <el-scrollbar style="height:100%">
          <div style=" text-align: center;">
            <span>{{ $t('cluster.detail.node.base_infomation') }}</span>
            <div align="center" style="margin-top: 15px">
              <table style="width: 90%" class="myTable">
                <tbody>
                  <tr>
                    <td>Name</td>
                    <td>{{ detaiInfo.name }}</td>
                  </tr>
                  <tr>
                    <td>CPU core</td>
                    <td>{{ detaiInfo.cpuCore }}</td>
                  </tr>
                  <tr>
                    <td>OS Image</td>
                    <td>{{ detaiInfo.os }}</td>
                  </tr>
                  <tr>
                    <td>OS Version</td>
                    <td>{{ detaiInfo.osVersion }}</td>
                  </tr>
                  <tr>
                    <td>Architecture</td>
                    <td>{{ detaiInfo.architecture }}</td>
                  </tr>
                  <tr>
                    <td>createdAt</td>
                    <td>{{ detaiInfo.createdAt | datetimeFormat }}</td>
                  </tr>
                  <tr>
                    <td>memory</td>
                    <td>{{ detaiInfo.memory }}</td>
                  </tr>

                  <tr>
                    <td>port</td>
                    <td>{{ detaiInfo.port }}</td>
                  </tr>
                  <tr>
                    <td>role</td>
                    <td>{{ detaiInfo.role }}</td>
                  </tr>
                  <tr>
                    <td>status</td>
                    <td>{{ detaiInfo.status }}</td>
                  </tr>
                  <tr>
                    <td>updatedAt</td>
                    <td>{{ detaiInfo.updatedAt | datetimeFormat }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <br>

          </div>
          <div slot="footer" class="dialog-footer">
            <el-button @click="dialogDetailVisible = false">{{ $t('commons.button.cancel') }}</el-button>
          </div>
        </el-scrollbar>
      </div>
    </el-dialog>

    <el-dialog @close="searchForPolling()" v-if='dialogLogVisible' :title="$t('cluster.condition.condition_detail')"
      width="70%" :visible.sync="dialogLogVisible">
      <ko-logs :operation="operationType" :clusterName="clusterName" :nodeName="nodeName" @retry="onRetry"
        @cancle="cancleLog()" />
    </el-dialog>

    <!-- <el-dialog :title="$t('cluster.detail.node.node_shrink')" width="30%" :visible.sync="dialogDeleteVisible">
      <el-form label-width="120px">
        <el-checkbox v-model="isForce">{{ $t('cluster.delete.is_force') }}</el-checkbox>
        <div style="margin-top: 5px"><span class="input-help">{{ $t('commons.confirm_message.force_delete') }}</span>
        </div>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button size="small" @click="dialogDeleteVisible = false">{{ $t("commons.button.cancel") }}</el-button>
        <el-button size="small" :v-loading="deleteLoadding" @click="submitDelete()">
          {{ $t("commons.button.submit") }}
        </el-button>
      </div>
    </el-dialog> -->

    <el-dialog :title="$t('cluster.detail.node.cordon')" width="50%" :visible.sync="dialogCordonVisible">
      <el-row type="flex" justify="center">
        <el-form label-width="120px">
          <el-form-item :label="$t('cluster.detail.node.mode')">
            <el-radio v-model="modeSelect" label="safe">{{ $t('cluster.detail.node.safe') }}</el-radio>
            <div><span class="input-help">{{ $t('cluster.detail.node.safe_cordon_help') }}</span></div>
            <el-radio v-model="modeSelect" label="force">{{ $t('cluster.detail.node.force') }}</el-radio>
            <div>
              <span class="input-help">{{ $t('cluster.detail.node.force_drain_help1') }}</span>
              <div><span class="input-help" style="margin-left: 20px">{{
                $t('cluster.detail.node.force_drain_help2')
              }}</span></div>
              <div><span class="input-help" style="margin-left: 20px">{{
                $t('cluster.detail.node.force_drain_help3')
              }}</span></div>
            </div>
          </el-form-item>
        </el-form>
      </el-row>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogCordonVisible = false">{{ $t('commons.button.cancel') }}</el-button>
        <el-button type="primary" :disabled="submitLoading" @click="submitCordon(true)">{{
          $t('commons.button.submit')
        }}</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import ComplexTable from "@/components/complex-table"

import { listNodeInTask } from "@/api/task/node"
// import KoLogs from "@/components/ko-logs/index.vue"
import Rule from "@/utils/rules"

export default {
  name: "ClusterNode",
  // components: { ComplexTable, KoLogs },
  components: { ComplexTable },
  data() {
    return {
      loading: false,
      submitLoading: false,
      buttons: [
        // {
        //   label: this.$t("commons.button.delete"),
        //   icon: "el-icon-delete",
        //   click: (row) => {
        //     this.onDelete(row)
        //   },
        //   disabled: (row) => {
        //     return this.provider === "" || this.buttonDisabled(row)
        //   },
        // },
      ],
      paginationConfig: {
        currentPage: 1,
        pageSize: 10,
        total: 0,
      },
      dialogCreateVisible: false,
      gpuExist: false,
      clusterName: "",
      selects: [],
      data: [],
      createForm: {
        hosts: [],
        nodes: [],
        increase: 1,
        statusId: "",
        supportGpu: "",
      },
      supportGpu: "",
      deleteForm: {
        nodes: "",
      },
      rules: {
        increase: [Rule.NumberRule],
        hosts: [Rule.RequiredRule],
      },
      dialogDetailVisible: false,
      detaiInfo: {
        metadata: {
          name: "",
          labels: [],
          labelsItem: [],
        },
        status: {
          nodeInfo: {},
          conditions: {},
        },
        spec: {},
      },
      // cluster logs
      dialogLogVisible: false,
      nodeName: "",
      operationType: "",

      // node delete
      currentNode: {},
      // dialogDeleteVisible: false,
      isForce: false,
      deleteRow: null,
      deleteLoadding: false,

      currentCluster: {},
      maxNodeNum: 256,
      hosts: [],
      provider: null,
      dialogCordonVisible: false,
      modeSelect: "safe",
      // namespaces: [],
      timer: null,
    }
  },
  methods: {
    getRowKeys(row) {
      return row.name
    },
    search() {
      this.loading = true
      this.$refs.nodeData?.clearSelection()
      const { currentPage, pageSize } = this.paginationConfig
      listNodeInTask(this.clusterName, currentPage, pageSize, false)
        .then((data) => {
          this.loading = false
          this.data = data.data || []
          this.paginationConfig.total = data.total
        })
        .catch(() => {
          this.loading = false
        })
    },
    searchForPolling() {
      const { currentPage, pageSize } = this.paginationConfig
      listNodeInTask(this.clusterName, currentPage, pageSize, true)
        .then((data) => {
          this.loading = false
          this.data = data.data || []
          this.paginationConfig.total = data.total
        })
        .catch(() => {
          this.loading = false
        })
    },
    buttonDisabled(row) {
      const onPolling = ["Initializing", "Terminating", "Waiting", "Terminating, SchedulingDisabled", "Creating"]
      if (row) {
        return onPolling.indexOf(row.status) !== -1
      } else {
        for (const node of this.selects) {
          if (onPolling.indexOf(node.status) !== -1) {
            return true
          }
        }
        return false
      }
    },
    create() {
      this.dialogCreateVisible = true
      if (this.provider === "bareMetal") {
        // listClusterResourcesAll(this.projectName, this.clusterName, "HOST").then((data) => {
        //   this.hosts = []
        //   data.items.forEach((item) => {
        //     if (item.status === "Running" && item.clusterId === "") {
        //       this.hosts.push(item)
        //     }
        //   })
        // })
      }
      this.maxNodeNum = this.currentCluster.spec.maxNodeNum - this.data.length
    },
    getDetailInfo(row) {
      this.detaiInfo = row
      this.dialogDetailVisible = true
    },
    resetForm(formName) {
      this.$refs[formName].resetFields()
    },

    // onDelete(row) {
    //   this.isForce = false
    //   this.dialogDeleteVisible = true
    //   if (row) {
    //     this.deleteRow = row
    //   } else {
    //     this.deleteRow = null
    //   }
    // },
    onCordon(operation) {
      if (operation === "cordon") {
        for (const item of this.selects) {
          if (item.status !== "Running") {
            this.$message({ type: "info", message: this.$t("cluster.detail.node.existing_cordoned") })
            return
          }
        }
        this.dialogCordonVisible = true
      } else {
        for (const item of this.selects) {
          if (item.status !== "Running, SchedulingDisabled") {
            this.$message({ type: "info", message: this.$t("cluster.detail.node.existing_actived") })
            return
          }
        }
        this.$confirm(this.$t("commons.confirm_message.uncordon"), this.$t("commons.message_box.prompt"), {
          confirmButtonText: this.$t("commons.button.confirm"),
          cancelButtonText: this.$t("commons.button.cancel"),
          type: "warning",
        }).then(() => {
          this.submitCordon(false)
        })
      }
    },
    getInternalIp(item) {
      return item.ip ? item.ip : "N/a"
    },
    // cluster logs
    getStatus(row) {
      if (row.status.indexOf("Terminating") !== -1) {
        this.operationType = "terminal-node"
      }
      if (row.status.indexOf("Failed") !== -1) {
        this.operationType = row.preStatus === "Initializing" ? "add-worker" : "terminal-node"
      }
      if (row.status.indexOf("Initializing") !== -1) {
        this.operationType = "add-worker"
      }
      this.dialogLogVisible = true
      this.currentNode = row
      this.nodeName = row.name
    },
    cancleLog() {
      this.searchForPolling()
      this.dialogLogVisible = false
    },

    polling() {
      this.timer = setInterval(() => {
        let flag = false
        const needPolling = ["Initializing", "Terminating", "Waiting", "Terminating, SchedulingDisabled", "Creating"]
        for (const item of this.data) {
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
  created() {
    this.clusterName = this.$route.params.name
    this.projectName = this.$route.params.project
    // this.getCluster()
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
  height: 450px;

  ::v-deep .el-scrollbar__wrap {
    height: 100%;
    overflow-x: hidden;
  }
}
</style>
