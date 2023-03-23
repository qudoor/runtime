<template>
  <layout-content>
    <div>
      <el-form ref="form" label-position='left' label-width="220px" :model="form" :rules="rules">
        <fu-steps ref="steps" footerAlign="right" finish-status="success" :beforeLeave="beforeLeave" @finish="onSubmit"
          @cancel="onCancel" :isLoading="loading" showCancel>
          <fu-step id="cluster-info" :title="$t('runtime.creation.step1')">
            <!-- <div class="example">
              <el-scrollbar style="height:100%;overflow-x: hidden"> -->
                <el-card>
                  <el-row>
                    <el-col :span="20">
                      <el-form-item :label="$t('runtime.creation.name')" prop="name">
                        <el-input v-model="form.name" clearable></el-input>
                        <div v-if="!nameValid"><span class="input-error">{{
                          $t('runtime.creation.name_invalid_err')
                        }}</span></div>
                        <div><span class="input-help">{{ $t('runtime.creation.name_help') }}</span></div>
                      </el-form-item>
                      <el-form-item label="量子产品" prop="quProductName">
                        <el-select style="width: 100%" @change="changeQuproduct" v-model="form.quProductName">
                          <el-option v-for="item of quProducts" :key="item.name" :value="item">{{ item.name }}
                          </el-option>
                        </el-select>
                      </el-form-item>


                      <el-form-item :label="$t('runtime.creation.arch')" prop="architectures">
                        <el-select style="width: 100%" @change="changeArch" v-model="form.architectures" clearable>
                          <el-option v-for="item of archs" :key="item" :value="item" :label="item">{{ item }}
                          </el-option>
                          <el-option v-if="archs.length > 1" value="all" label="MIXED">MIXED</el-option>
                        </el-select>
                        <div v-if="!archValid"><span class="input-error">{{ $t('runtime.creation.repo_err') }}</span>
                        </div>
                      </el-form-item>

                      <el-form-item :label="$t('runtime.creation.yum_repo')" prop="yumOperate">
                        <el-select style="width: 100%" v-model="form.yumOperate">
                          <el-option v-for="item of selectProduct.spec.yumOperator" :key="item" :value="item"
                            :label="item">{{ item }} </el-option>
                        </el-select>
                      </el-form-item>

                      <el-form-item label="硬件类型" prop="processingUnit" v-if="showProcessingUnitSelect()">
                        <el-select style="width: 100%" @change="changeProcessingUnit" v-model="form.processingUnit"
                          clearable>
                          <el-option v-for="item of form.supportProcessingUnit" :key="item" :value="item" :label="item">{{
                            item }} </el-option>
                        </el-select>
                      </el-form-item>

                    </el-col>
                    <el-col :span="4"><br /></el-col>
                  </el-row>
                </el-card>
              <!-- </el-scrollbar>
            </div> -->
          </fu-step>

          <fu-step id="select-env-version" :title="selectVersionLabel">
            <el-card>
              <el-row>
                <el-col :span="24">
                  <el-form-item :label="item.name" :prop="genVersionLabel(item.name)" :key="key"
                    v-for="(item, key) of selectArray">
                    <el-select style="width: 100%" v-model.trim="form[genVersionLabel(item.name)]">
                      <el-option v-for="ver of item.versions" :key="ver" :value="ver">{{ ver }} </el-option>
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>
            </el-card>
          </fu-step>

          <fu-step id="node-setting" :title="$t('runtime.creation.step2')">
            <!-- <div class="example"> -->
            <!-- <el-scrollbar style="height:100%"> -->
            <el-card>
              <el-form-item label="Master 节点" prop="masters">
                <el-select multiple filterable style="width: 100%" @change="toggle('master')" v-model="form.masters"
                  clearable>
                  <el-option v-for="item of hosts" :key="item.label" :label="item.label" :value="item.value">
                  </el-option>
                </el-select>
                <div><span class="input-help">{{ $t('cluster.creation.master_select_help') }}</span></div>
              </el-form-item>
              <el-form-item label="Worker 节点" prop="workers">
                <el-select multiple filterable style="width: 100%" @change="toggle('worker')" v-model="form.workers"
                  clearable>
                  <el-option v-for="item of hosts" :key="item.label" :label="item.label" :value="item.value">
                  </el-option>
                </el-select>
                <div v-if="isNodeNumExceed()">
                  <span class="input-error">{{ $t('cluster.creation.node_number_help', [form.maxNodeNum]) }}</span>
                </div>
              </el-form-item>

            </el-card>
            <!-- </el-scrollbar> -->
            <!-- </div> -->
          </fu-step>

          <fu-step :title="$t('runtime.creation.step7')" id="overview">
            <!-- <div class="example">
              <el-scrollbar style="height:100%"> -->
                <el-card>
                  <el-divider content-position="left">{{ $t('runtime.creation.base_setting') }}</el-divider>
                  <el-row type="flex" justify="center">
                    <el-col :span="6">
                      <ul>{{ $t('runtime.creation.name') }}</ul>
                      <!-- <ul>{{ $t('runtime.creation.version') }}</ul> -->
                      <ul>{{ $t('runtime.creation.arch') }}</ul>
                      <ul>{{ $t('runtime.creation.yum_repo') }}</ul>
                      <ul> 量子产品 </ul>
                      <ul> 硬件单元 </ul>
                    </el-col>
                    <el-col :span="6">
                      <ul>{{ form.name }}</ul>
                      <!-- <ul>{{ form.version }}</ul> -->
                      <ul>{{ form.architectures }}</ul>
                      <ul>{{ form.yumOperate }}</ul>
                      <ul>{{ form.quProductName }}</ul>
                      <ul>{{ form.processingUnit }}</ul>
                    </el-col>
                  </el-row>

                  <el-divider content-position="left">{{ selectVersionLabel }}</el-divider>
                  <el-row :key="key" type="flex" justify="center" v-for="(item, key) of selectArray">
                    <el-col :span="6">
                      <ul>{{ item.name }}</ul>
                    </el-col>
                    <el-col :span="6">
                      <ul>{{ form[genVersionLabel(item.name)] }}</ul>
                    </el-col>
                  </el-row>

                  <el-divider content-position="left">{{ $t('runtime.creation.step2') }}</el-divider>
                  <el-row type="flex" justify="center">
                    <el-col :span="6">
                      <ul>{{ 'Master 节点 ' }}</ul>
                    </el-col>
                    <el-col :span="6">
                      <ul v-for="item of form.masters" :key="item">{{ getNodeLabelByName(item) }}</ul>
                    </el-col>
                  </el-row>

                  <el-row type="flex" justify="center">
                    <el-col :span="6">
                      <ul>{{ 'Worker 节点 ' }}</ul>
                    </el-col>
                    <el-col :span="6">
                      <ul v-for="item of form.workers" :key="item">{{ getNodeLabelByName(item) }}</ul>
                    </el-col>
                  </el-row>

                  <br>
                </el-card>
              <!-- </el-scrollbar>
            </div> -->
          </fu-step>
        </fu-steps>
      </el-form>
    </div>
  </layout-content>
</template>

<script>
import LayoutContent from "@/components/layout/LayoutContent"
import { listHostsByQuproduct } from "@/api/hosts"
import { listRegistryAll } from "@/api/runtime-system-setting"
import { createTask, checkClusterNameExistence, listTask, getDependentsByArchAndQuproduct } from "@/api/task"
import Rule from "@/utils/rules"
// import _ from "lodash"

export default {
  name: "ClusterCreate",
  components: { LayoutContent },
  data() {
    return {
      form: {
        name: "",
        version: "",
        architectures: "",
        quProductName: "",
        yumOperate: "",
        dependents: [],
        masters: [],
        workers: [],
        nodes: [],
        // processingUnit: '',// GPU: 安装 ipce; CPU: 安装 QuTrunk 类型
        supportProcessingUnit: [],
      },
      rules: {
        name: [Rule.ClusterNameRule],
        version: [Rule.RequiredRule],
        quProductName: [Rule.RequiredRule],
        projectName: [Rule.RequiredRule],
        provider: [Rule.RequiredRule],
        architectures: [Rule.RequiredRule],
        yumOperate: [Rule.RequiredRule],
        runtimeType: [Rule.RequiredRule],
        masters: [Rule.RequiredRule],
        // processingUnit: [Rule.RequiredRule],
      },
      archs: [],
      versions: [],
      nameValid: true,
      archValid: true,
      nodes: "",
      plans: [],
      allHosts: [],
      hosts: [],
      scheduleType: true,
      // projects: [],
      quProducts: [],
      selectProduct: {
        "id": "",
        "name": "",
        "spec": {
          "arch": [],
          "version": "",
          "dependents": [],
          "yumOperator": []
        }
      },
      selectVersion: [],
      selectArray: [],
      // yumOperates: [],
      repoList: [],
      validateCluster: false,
      loading: false,
      // helmVersions: ["v3", "v2"],
      selectVersionLabel: "选择版本",
      masters: [],
      workers: [],
    }
  },
  methods: {
    getNodeLabelByName(name) {
      let res = name
      this.hosts.map(item => {
        if (item.value === name) {
          res = item.label
        }
      })
      return res
    },
    checkFormValidate() {
      let bool
      this.$refs["form"].validate((valid) => {
        if (valid) {
          if (this.form.masters) {
            const lenMaster = this.form.masters.length
            if (lenMaster !== 0) {
              if (lenMaster !== 1 && lenMaster !== 3) {
                this.$message({ type: "info", message: this.$t("cluster.creation.master_select_help") })
                return false
              }
            }
            if (this.isNodeNumExceed()) {
              return false
            }
          }
          if (this.form.kubeServiceNodePortRange1 > this.form.kubeServiceNodePortRange2) {
            return false
          }
          bool = true
        } else {
          bool = false
        }
      })
      return bool
    },
    async loadRegistry() {
      await listRegistryAll().then((data) => {
        this.repoList = data.items === null ? [] : data.items
      })
    },
    setRules(arr) {
      const newRules = arr.reduce((acc, name) => {
        const versionLabel = this.genVersionLabel(name);
        console.log('acc :>> ', acc);
        acc[versionLabel] = [Rule.RequiredRule]
        return acc
      }, { ...this.rules })

      // this.rules = newRules // 对 this.rules 进行了重新赋值，导致 el-form 组件重新渲染，从而触发了验证
      Object.assign(this.rules, newRules)
      console.log("this.rules: ", this.rules);
    },
    setDependentsToForm(dependents) {
      dependents.map(name => {
        name = this.genVersionLabel(name)
        this.$set(this.form, name, '') // 注意：不能直接为对象添加新的属性，因为新增的属性不会被监听
      })
    },
    changeQuproduct(quProductObj) {
      delete this.form.processingUnit
      this.selectProduct = quProductObj
      this.form.yumOperate = quProductObj?.spec?.yumOperator[0] || ''
      this.form.quProductName = quProductObj.name
      this.form.supportProcessingUnit = quProductObj?.spec?.supportProcessingUnit || []
      this.archs = [...quProductObj?.spec?.arch]
      console.log('quProductObj :>> ', quProductObj);

      const willSetRules = [...quProductObj?.spec?.dependents]
      if (this.showProcessingUnitSelect()) {
        willSetRules.push('processingUnit')
        this.form.processingUnit = this.form.supportProcessingUnit[0]
      }
      this.setRules(willSetRules)

      this.setDependentsToForm(quProductObj?.spec?.dependents)

      if (this.archs.length > 0) {
        this.changeArch(this.archs[0])
        this.form.architectures = this.archs[0]
      }
    },
    changeProcessingUnit() {
      this.form.masters = []
      this.form.workers = []
    },
    loadQuProducts() {
      listTask().then((data) => {
        // 拆分版本 架构 量子应用名字， 分别选择，如果量子产品太多的话方便用户选择
        this.quProducts = data
      })
    },
    loadHosts() {
      this.allHosts = []
      listHostsByQuproduct(this.selectProduct.name).then((data) => {
        console.log('listHostsByQuproduct data: ', data);
        if (data.items !== null) {
          for (const h of data.items) {
            if (h.status === "Running" && !h.appEnvId) {
              // this.allHosts.push({ name: h.name, architectures: h.architectures, ip: h.ip, id: h.id })
              this.allHosts.push(h)
            }
          }
        }
        this.changeArch(this.form.architectures)
      })
    },
    async loadVersion() {
      if (!this.form.architectures || !this.form.quProductName) return
      await getDependentsByArchAndQuproduct(this.form.architectures, this.form.quProductName).then((data) => {
        console.log('getDependentsByArchAndQuproduct data :>> ', data);
        let tempArr = []
        for (let i in data) {
          const versions = data[i].map(item => item['version'])
          tempArr.push({ 'name': i, 'versions': [...versions] })
          console.log('data[i] :>> ', data[i]);
        }
        this.selectArray = [...tempArr]

        console.log('依赖 this.selectArray :>> ', this.selectArray);
        console.log('tempFormData this.form :>> ', this.form);
      })


      // 默认选中第一个版本
      this.selectArray.map(item => {
        let name = this.genVersionLabel(item.name)
        this.form[name] = item.versions[0]
      })

    },
    beforeLeave(step, isNext) {
      console.log('step:', step)
      if (step.id === "cluster-info") {
        this.loadHosts()
      }
      if (!isNext) {
        return
      }
      if (this.checkFormValidate()) {
        if (this.validateCluster !== true) {
          if (step.index === 0) {
            setTimeout(() => {
              checkClusterNameExistence(this.form.name).then(
                (data) => {
                  if (!data.isExist && this.archValid) {
                    this.nameValid = true
                    this.loading = false
                    this.validateCluster = true
                    this.$refs.steps.next()
                    return true
                  } else {
                    this.nameValid = !data.isExist
                    this.loading = false
                    return false
                  }
                },
                () => {
                  this.nameValid = true
                  this.loading = false
                  this.validateCluster = true
                  this.$refs.steps.next()
                  return true
                }
              )
            }, 1000)
            this.loading = true
            return false
          } else {
            this.validateCluster = true
            this.$refs.steps.next()
            return false
          }
        } else {
          return true
        }
      } else {
        return false
      }
    },
    isNodeNumExceed() {
      return this.form.workers.length + this.form.masters.length > this.form.maxNodeNum
    },
    showProcessingUnitSelect() {
      console.log('this.form.supportProcessingUnit :>> ', this.form.supportProcessingUnit);
      return this.form.supportProcessingUnit.length > 1
    },
    onSubmit() {
      let dependents = []
      this.selectArray.map(item => {
        let obj = {}
        let name = this.genVersionLabel(item.name)
        obj[name] = this.form[name]
        dependents.push(obj)
      })

      let request_data = {
        "name": this.form.name,
        "quproduct": this.form.quProductName,
        "spec": {
          "version": this.form.version,
          "architectures": this.form.architectures,
          // "registryId": this.getRegistryId(type), // 混合架构的时候怎么存？这个栏位作用是？
          // "maxNodeNum": 0,
          "masterHostIds": this.getMasterHostIds(),
          "slaveHostIds": this.getWorksHostIds(),
          // "upgradeVersion": "string",
          "yumOperate": this.form.yumOperate
        },
        // "source": "string",
        "dependents": dependents,
        "nodes": this.form.nodes,
        "processingUnit": this.form.processingUnit
      }

      console.log('request_data: ', request_data)
      createTask(request_data).then(() => {
        this.$router.push({ name: "TaskList" })
      })
    },
    getMasterHostIds() {
      let hostIds = []
      this.form.masters.map(item => {
        let findHost = this.allHosts.find(host => host.name === item)
        if (findHost) hostIds.push(findHost['id'])
      })
      console.log('hostIds :>> ', hostIds);
      return hostIds
    },
    getWorksHostIds() {
      let hostIds = []
      this.form.workers.map(item => {
        let findHost = this.allHosts.find(host => host.name === item)
        if (findHost) hostIds.push(findHost['id'])
      })
      console.log('hostIds :>> ', hostIds);
      return hostIds
    },
    changeArch(type) {
      console.log("type: ", type, "this.allHosts: ", this.allHosts)
      this.hosts = []
      this.archValid = true
      let isAmdExit = false
      let isArmExit = false
      switch (type) {
        case "amd64":
        case "x86_64":
          this.setSelectHosts('x86_64')
          for (const repo of this.repoList) {
            if (repo.architecture === "x86_64") {
              isAmdExit = true
              break
            }
          }
          this.archValid = isAmdExit
          break
        case "arm64":
          this.setSelectHosts('aarch64')
          for (const repo of this.repoList) {
            if (repo.architecture === "aarch64") {
              isArmExit = true
              break
            }
          }
          this.archValid = isArmExit
          break
        case "all":
          this.setSelectHosts('all')
          for (const repo of this.repoList) {
            if (repo.architecture === "x86_64") {
              isAmdExit = true
              continue
            }
            if (repo.architecture === "aarch64") {
              isArmExit = true
              continue
            }
          }
          this.archValid = isAmdExit && isArmExit
          break
      }
      this.loadVersion()
    },
    setSelectHosts(architecture) {
      let tempAllHosts = [...this.allHosts]
      // if (this.form.processingUnit === 'GPU') {
      //   tempAllHosts = this.allHosts.filter(item => item.hasGpu)
      // }
      console.log('tempAllHosts :>> ', tempAllHosts);

      if (architecture === 'all') {
        for (const h of tempAllHosts) {
          this.hosts.push({ label: h.name + "(" + h.ip + ")", value: h.name })
        }
      } else {
        for (const h of tempAllHosts) {
          console.log('architecture :>> ', h.architecture);
          if (h.architecture === architecture) {
            this.hosts.push({ label: h.name + "(" + h.ip + ")", value: h.name })
          }
        }
      }
    },
    toggle(role) {
      this.form.nodes = []
      switch (role) {
        case "worker": {
          let delw = []
          this.form.masters.forEach((m) => {
            this.form.workers.forEach((w) => {
              if (m === w) {
                delw.push(w)
              }
            })
          })
          let cw = [].concat(this.form.workers)
          console.log('cw :>> ', cw, 'delw: ', delw);
          delw.forEach((d) => {
            cw.splice(cw.indexOf(d), 1)
            this.form.workers = cw
          })
          if (this.form.workers.length === 0) {
            this.scheduleType = true
            this.form.masterScheduleType = "enable"
          } else {
            this.scheduleType = false
          }
          break
        }
        case "master": {
          let delm = []
          this.form.workers.forEach((m) => {
            this.form.masters.forEach((w) => {
              if (m === w) {
                delm.push(w)
              }
            })
          })
          let cm = [].concat(this.form.masters)
          console.log('cm :>> ', cm, 'delm: ', delm);
          delm.forEach((d) => {
            cm.splice(cm.indexOf(d), 1)
            this.form.masters = cm
          })
          break
        }
      }
      this.form.masters.forEach((n) => {
        this.form.nodes.push({ hostName: n, role: "master" })
      })
      this.form.workers.forEach((n) => {
        this.form.nodes.push({ hostName: n, role: "worker" })
      })

      console.log('this.form :>> ', this.form);
    },
    getHostName(hosts) {
      return hosts.join(",")
    },
    genVersionLabel(depName) {
      if (depName === 'processingUnit') return depName
      return depName + '_version'
    },
    isMultiMaster() {
      if (this.form.provider === "plan") {
        if (this.form.plan === "") {
          return false
        }
        for (const p of this.plans) {
          if (p.name === this.form.plan) {
            return p.deployTemplate !== "SINGLE"
          }
        }
      } else {
        return this.form.masters.length === 3
      }
    },
    onCancel() {
      this.$router.push({ name: "TaskList" })
    },

  },
  async created() {
    this.loadQuProducts()
    await this.loadRegistry()
    // this.initSelect()
    this.changeQuproduct(this.quProducts[0])
  }
}
</script>
<style lang="scss" scoped>
.example {
  min-height: 350px;
  margin: 1% 10%;

  ul {
    height: 20px;
  }

  ::v-deep .el-scrollbar__wrap {
    height: 100%;
    overflow-x: hidden;
  }
}
</style>




