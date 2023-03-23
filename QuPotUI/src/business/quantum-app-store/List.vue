<template>
  <layout-content :header="'量子应用列表'" :back-to="{ name: 'QuantumAppStoreClusterList' }">
    <div>
      <el-row>
        <!-- <el-tooltip placement="top-start">
          <div slot="content">
            {{ $t('cluster.detail.tool.sync_tool_help1') }}<br />
            <li>{{ $t('cluster.detail.tool.sync_tool_help2') }}</li>
            <li>{{ $t('cluster.detail.tool.sync_tool_help3') }}</li>
          </div>
          <el-button v-if="!syncStatus" style="margin-left:10px" icon="el-icon-refresh-left" @click="syncToolStatus">
            {{ $t('cluster.detail.tool.sync_tool') }}</el-button>
          <el-button v-if="syncStatus" style="margin-left:10px" icon="el-icon-loading" disabled>
            {{ $t('commons.status.synchronizing') }}...</el-button>
        </el-tooltip> -->

        <div v-loading="loading" v-for="app in appList" :key="app.name">
          <el-col :span="6">
            <el-card style="margin-left:10px; margin-top:10px; height: 180px" class="box-card">
              <el-row>
                <el-col :span="8">
                  <img v-if="app.icon" style="width: 60px; height: 60px" :src="app.icon">
                  <img v-else style="width: 60px; height: 60px" :src="require('@/assets/apps.svg')">
                </el-col>
                <el-col :span="16">
                  <div><span>{{ app.name }} - {{ app.version }}</span></div>
                  <div style="margin-top: 30px;"><span class="text-line-clamp">{{ app.description }}</span></div>
                </el-col>
              </el-row>
              <el-divider></el-divider>
              <div v-if="app.status === 'Waiting'">
                <el-button size="small" @click="onEnable(app)" style="float:right; margin: 5px">
                  {{ $t('commons.button.enable') }}
                </el-button>
              </div>
              <!-- <div v-if="app.status === 'Failed'">
                <el-button size="small" @click="onErrorShow(app)" style="float:right; margin: 5px">
                  {{ $t('commons.button.error_msg') }}
                </el-button>
                <el-button size="small" @click="onEnable(app)" style="float:right; margin: 5px">
                  {{ $t('commons.button.enable') }}
                </el-button>
              </div> -->
              <div v-if="app.status === 'Running'">
                <!-- <span v-if="!app.frame" style="float:right; margin: 12px">{{ $t('commons.status.running') }}</span> -->
                <span v-if="app.proxyType !== 'nodeport'" style="float:right; margin: 12px">{{
                    $t('commons.status.running')
                }}</span>
                <el-button v-if="app.proxyType === 'nodeport'" size="small" @click="openFrame(app)"
                  style="float:right; margin: 5px">
                  {{ $t('commons.button.jump_to') }}
                </el-button>
                <el-button size="small" @click="onDisable(app)" style="float:right; margin: 5px">
                  {{ $t('commons.button.disable') }}
                </el-button>
              </div>
              <!-- <div v-if="app.status === 'Initializing'">
                <span style="float:right; margin: 12px">{{ $t('commons.status.initializing') }}
                  <i class="el-icon-loading"></i>
                </span>
              </div>
              <div v-if="app.status === 'Upgrading'">
                <span style="float:right; margin: 12px">{{ $t('commons.status.upgrading') }}
                  <i class="el-icon-loading"></i>
                </span>
              </div>
              <div v-if="app.status === 'Terminating'">
                <span style="float:right; margin: 12px">{{ $t('commons.status.terminating') }}
                  <i class="el-icon-loading"></i>
                </span>
              </div>
              <el-button v-if="app.higher_version && app.status === 'Running'" @click="onUpgrade(app)" size="small"
                style="float:right; margin: 5px">{{ $t('commons.button.upgrade') }}
              </el-button> -->
            </el-card>
          </el-col>
        </div>
      </el-row>

      <el-dialog :title="'启用 ' + appForm['name']" width="50%" :close-on-click-modal="false"
        :visible.sync="dialogEnableVisible">
        <el-form label-position='left' :model="appForm" ref="appForm" label-width="180px">

          <el-form-item :label="'资源要求'" prop="resource_require" :rules="requiredRules">
            <el-select style="width: 90%" filterable v-model="appForm['resource_require']" clearable value-key="id"
              :rules="requiredRules">
              <el-option v-for="item of resourceLimitsOptions" :label="item.label" :key="item.id" :value="item">
                {{ item.label }}
              </el-option>
            </el-select>
          </el-form-item>

          <!-- <el-form-item :label="'CPU 核心数'" prop="cpu_require" :rules="numberRules">
            <el-input-number :step="1" v-model="appForm['cpu_require']" clearable></el-input-number>
          </el-form-item>

          <el-form-item :label="'内存'" prop="memory_require" :rules="numberRules">
            <el-input-number :step="1" :max="65535" step-strictly v-model="appForm['memory_require']" clearable>
            </el-input-number>
          </el-form-item> -->

          <el-form-item :label="'域名'" prop="domain" :rules="requiredRules">
            <el-input style="width: 90%" v-model="appForm['domain']" clearable></el-input>
          </el-form-item>

          <el-form-item :label="'服务端口（serverPort）'" prop="server_port" :rules="requiredRules">
            <el-input-number :step="1" :max="65535" step-strictly v-model.number="appForm['server_port']" clearable>
            </el-input-number>
          </el-form-item>
          <el-form-item :label="'架构'" prop="arch" :rules="requiredRules">
            <el-select style="width: 90%" filterable v-model="appForm['arch']" clearable>
              <el-option v-for="item of archs" :key="item" :value="item">{{ item }}</el-option>
            </el-select>
          </el-form-item>

          <div v-if="isQuFinanceApp(appForm.name)">
            <el-form-item :label="'VPN 链接'" prop="vpn_url" :rules="requiredRules">
              <el-input style="width: 90%" v-model="appForm['vpn_url']" clearable></el-input>
            </el-form-item>
          </div>

        </el-form>
        <div slot="footer" class="dialog-footer">
          <el-button @click="dialogEnableVisible = false">{{ $t('commons.button.cancel') }}</el-button>
          <el-button type="primary" @click="enable()" v-preventReClick>{{ $t('commons.button.ok') }}</el-button>
        </div>
      </el-dialog>

      <el-dialog :title="$t('cluster.detail.tool.err_title')" width="50%" :visible.sync="dialogErrorVisible">
        <div style="margin: 0 50px"><span style="line-height: 30px">{{ conditions | errorFormat }}</span></div>
        <div slot="footer" class="dialog-footer">
          <el-button v-if="appForm.status == 'Failed'" @click="disable(appForm, 'Failed')" v-preventReClick>
            {{ $t('commons.button.disable') }}</el-button>
          <el-button @click="dialogErrorVisible = false">{{ $t('commons.button.cancel') }}</el-button>
        </div>
      </el-dialog>

      <el-dialog :title="$t('cluster.detail.tool.info_title')" width="30%" :visible.sync="dialogDisableVisible">
        <span>{{ $t('cluster.detail.tool.disable_show_msg') }}</span>
        <div slot="footer" class="dialog-footer">
          <el-button @click="dialogDisableVisible = false">{{ $t('commons.button.cancel') }}</el-button>
          <el-button type="primary" @click="disable(appForm, 'Running')">{{ $t('commons.button.ok') }}</el-button>
        </div>
      </el-dialog>

      <el-dialog :title="$t('cluster.detail.tool.upgrade_title')" width="30%" :visible.sync="dialogUpgradeVisible">
        <span>{{ appForm.name }}: {{ appForm.version }} ---> {{ appForm.higher_version }}</span>
        <div slot="footer" class="dialog-footer">
          <el-button @click="dialogUpgradeVisible = false">{{ $t('commons.button.cancel') }}</el-button>
          <el-button type="primary" @click="upgrade(appForm)" v-preventReClick>{{ $t('commons.button.ok') }}
          </el-button>
        </div>
      </el-dialog>
    </div>
  </layout-content>
</template>

<script>
import { getAppList, createApp } from '@/api/quantum-app-store'
import { getClusterByName } from "@/api/cluster"
import Global from "@/utils/global_variable"
import { is_web_uri } from "valid-url"
import isValidDomain from 'is-valid-domain'
import LayoutContent from "@/components/layout/LayoutContent"
import Rule from "@/utils/rules"

export default {
  name: "ClusterTool",
  props: ["cluster"],
  components: { LayoutContent },
  data() {
    return {
      loading: false,
      clusterName: "",
      currentCluster: {
        name: "",
        spec: {
          architectures: "",
        },
      },
      appList: [],
      dialogEnableVisible: false,
      dialogErrorVisible: false,
      dialogDisableVisible: false,
      dialogUpgradeVisible: false,
      conditions: "",
      isPasswordValid: true,
      isReplicasValid: true,
      appForm: {
        name: "",
        appVersion: "",
        description: "",
        status: "",
        digest: "",
        url: "",
        cpu_require: "",
        memory_require: "",
        vpn_url: "",
        domain: "",
        // resource_require_label: "",
        resource_require: {},
      },
      numberRules: [Rule.NumberRule],
      requiredRules: [Rule.RequiredRule],
      passwordRules: [Rule.PasswordRule],
      namespaces: [],
      nodes: [],
      nodeNum: 0,
      storages: [],
      archs: ["amd64", "arm64"],
      syncStatus: false,
      flexStatus: null,
      timer: null,
      resourceLimitsOptions: [
        { label: "CPU 128m; 内存 256Mi", value: { cpu_require: '128m', memory_require: '256Mi', }, id: 1 },
        { label: "CPU 256m; 内存 512Mi", value: { cpu_require: '256m', memory_require: '512Mi', }, id: 2 },
        { label: "CPU 512m; 内存 1024Mi", value: { cpu_require: '516m', memory_require: '1024Mi', }, id: 3 },
      ]
      // resourceLimitsOptions: ["xiao", 'zhogn', 'laksdjfl']
    }
  },
  methods: {
    search() {
      getClusterByName(this.clusterName).then((data) => {
        this.currentCluster = data
        // this.getFlexIp()
      })
      this.loadTool()
    },
    installApp() {
      this.formatResourceDataForRequestData()
      console.log('this.appForm :>> ', this.appForm);
      createApp(this.clusterName, this.appForm['name'], this.appForm).then((data) => {
        if (data.success) {
          this.dialogEnableVisible = false
          this.search()
        } else {
          this.$message({ type: "error", message: data?.msg || "创建失败" })
        }
      })
    },
    formatResourceDataForRequestData() {
      this.appForm['cpu_require'] = this.appForm['resource_require']['value']['cpu_require']
      this.appForm['memory_require'] = this.appForm['resource_require']['value']['memory_require']
    },
    loadTool() {
      this.loading = true
      getAppList(this.clusterName)
        .then((res) => {
          this.loading = false
          // for (const i in res.data) {
          //   i['resource_require'] = {}
          // }
          console.log("quantum app store data: ", res.data)
          this.appList = res.data
        }).catch(() => {
          this.loading = false
        })
    },
    openFrame(item) {
      console.log('item.url :>> ', item.url);
      window.open(item.url, "_blank")
    },
    onEnable(item) {
      console.log("item: ", item)
      // let QuantumApp = Global.QuantumApp
      // console.log('item.name: ', QuantumApp['qufinance']);
      // switch (item.name) {
      //   case QuantumApp['qubox-demo']:
      //     console.log('item.name: ', QuantumApp['qubox-demo']);
      //     break
      //   case QuantumApp['qufinance']:
      //     console.log('item.name: ', QuantumApp['qufinance']);
      //     break
      //   case QuantumApp['qusprout']:
      //     console.log('item.name: ', QuantumApp['qusprout']);
      //     break
      //   //   case "loki":
      //   //     if (this.currentCluster.spec.architectures === "amd64") {
      //   //       for (const app of this.appList) {
      //   //         if (app.name === "logging") {
      //   //           this.conditions = app.status === "Waiting" ? "" : this.$t("cluster.detail.app.log_err_msg")
      //   //           break
      //   //         }
      //   //       }
      //   //     }
      //   //     break
      // }
      this.appForm = item
      // if (this.conditions === "") {
      //   this.listNamespaces()
      //   this.listStorages()
      //   this.setDefaultVars(item)
      this.setDefaultValue(item)
      //   this.isPasswordValid = true
      //   this.isReplicasValid = true
      this.dialogEnableVisible = true
      // } else {
      // this.dialogErrorVisible = true
      // }
    },
    enable() {
      console.log("enable: ", this.appForm)
      console.log("this: ", this)
      this.$refs["appForm"].validate((valid) => {
        console.log('valid :>> ', valid);
        if (valid && this.checkDomain() && this.isVpnUrlValid()) {
          this.installApp()
        } else {
          return false
        }
      })
    },
    checkDomain() {
      console.log('this.appForm :>> ', this.appForm);
      let validRes = isValidDomain(this.appForm['domain'])
      if (!validRes) {
        this.$message({ type: "error", message: "请输入正确的域名" })
      }
      return validRes
    },
    isVpnUrlValid() {
      let validRes = is_web_uri(this.appForm['vpn_url'])
      if (!validRes) {
        this.$message({ type: "error", message: "请输入正确的 VPN 链接" })
      }
      return validRes
    },
    // enableFlexIp() {
    //   enableFlex(this.clusterName).then(() => {
    //     this.search()
    //     this.$message({ type: "success", message: this.$t("commons.msg.op_success") })
    //   })
    // },
    isQuFinanceApp(name) {
      return name === Global.QuantumApp['qufinance']
    },
    // disableFlexIp() {
    //   disableFlex(this.clusterName).then(() => {
    //     this.search()
    //     this.$message({ type: "success", message: this.$t("commons.msg.op_success") })
    //   })
    // },
    // getFlexIp() {
    //   getFlex(this.clusterName).then((res) => {
    //     this.flexStatus = res === this.currentCluster.spec.kubeRouter ? "enable" : "disable"
    //   })
    // },
    setDefaultValue(item) {
      let QuantumApp = Global.QuantumApp
      item.server_port = '80'
      switch (item.name) {
        case QuantumApp['qubox-demo']:
          console.log('item.name: ', QuantumApp['qubox-demo']);
          item.domain = 'qubox-demo.queco.cn'
          break
        case QuantumApp['qufinance']:
          console.log('item.name: ', QuantumApp['qufinance']);
          item.domain = 'qufinance.queco.cn'
          item.vpn_url = 'http://x.x.x.202:7890'
          break
        case QuantumApp['qusprout']:
          console.log('item.name: ', QuantumApp['qusprout']);
          // item.domain = 'qubox-demo.queco.cn'
          break
      }
    },
    onErrorShow(item) {
      this.appForm = item
      this.conditions = item.message
      this.dialogErrorVisible = true
    },
    onDisable(item) {
      this.appForm = item
      this.dialogDisableVisible = true
    },
    // eslint-disable-next-line no-unused-vars
    disable(item, status) {
      this.$message({ type: "info", message: "TODO" })
      // if (status === "Running") {
        // disableTool(this.clusterName, item).then(() => {
        //   this.dialogDisableVisible = false
        //   this.search()
        // })
      // } else {
        // disableTool(this.clusterName, item).then(() => {
        //   this.dialogErrorVisible = false
        //   this.search()
        // })
      // }
    },
    onUpgrade(item) {
      this.appForm = item
      this.dialogUpgradeVisible = true
    },
    syncToolStatus() {
      this.syncStatus = true
      this.syncStatus = false
    },
    polling() {
      this.timer = setInterval(() => {
        let flag = false
        const needPolling = ["Initializing", "Terminating", "Upgrading"]
        for (const item of this.appList) {
          if (needPolling.indexOf(item.status) !== -1) {
            flag = true
            break
          }
        }
        if (flag) {
          // listTool(this.clusterName).then((data) => {
          //   const currentLanguage = this.$store.getters.language || "zh-CN"
          //   this.appList = data
          //   for (const to of this.appList) {
          //     if (currentLanguage == "en-US") {
          //       to.describeInfo = to.describe.split("|")[1]
          //     } else {
          //       to.describeInfo = to.describe.split("|")[0]
          //     }
          //   }
          // })
          getAppList(this.clusterName)
            .then((res) => {
              console.log("quantum app store data: ", res)
              this.loading = false
              this.appList = res.data
            }).catch(() => {
              this.loading = false
            })

        }
      }, 10000)
    },
  },
  created() {
    this.clusterName = this.$route.params.cluster
    this.search()
    // this.loadTool()
    this.polling()
    // this.listNodes()
  },
  destroyed() {
    clearInterval(this.timer)
    this.timer = null
  },
}
</script>

<style scoped>
.text-line-clamp {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 1;
  overflow: hidden;
}
</style>
