<template>
  <div>
    <div class="dialog" v-loading="conditionLoading" :element-loading-text="$t('task.condition.condition_loading')"
      element-loading-spinner="el-icon-loading" element-loading-background="rgba(255, 255, 255, 1)"
      :style="{ height: dialogHeight }">
      <el-scrollbar style="height:90%">
        <span v-if="log.conditions && log.conditions.length === 0">{{ log.message | errorFormat }}</span>
        <div>
          <el-steps :space="50" style="margin: 0 50px" direction="vertical" :active="activeName">
            <el-step v-for="condition in log.conditions" :key="condition.name"
              :title="$t('task.condition.' + condition.name)">
              <i :class="loadStepIcon(condition.status)" slot="icon"></i>
              <el-collapse v-if="condition.status === 'False'" accordion slot="description" v-model="activeCollapse">
                <el-collapse-item :title="item.name" :name="index" v-for="(item, index) in condition.formatMsgs"
                  :key="index">
                  <template slot="title">
                    <div v-if="item.failed">{{ item.name }}</div>
                    <div v-if="!item.failed">{{ item.name }}</div>
                  </template>
                  <div v-if="item.type !== 'unFormat'">
                    <div v-if="item.info.cmd">
                      <div><span style="font-weight: bold">cmd</span></div>
                      <div><span style="white-space: pre-wrap;">{{ item.info.cmd }}</span></div>
                    </div>

                    <div v-if="item.info.msg">
                      <div><span style="font-weight: bold">message</span></div>
                      <div><span style="white-space: pre-wrap;">{{ item.info.msg }}</span></div>
                    </div>

                    <div v-if="item.info.stderr">
                      <div style="margin-top: 2px"><span style="font-weight: bold">stderr</span></div>
                      <div><span style="white-space: pre-wrap;">{{ item.info.stderr }}</span></div>
                    </div>

                    <div v-if="item.info.stdout">
                      <div style="margin-top: 2px"><span style="font-weight: bold">stdout</span></div>
                      <div><span style="white-space: pre-wrap;">{{ item.info.stdout }}</span></div>
                    </div>
                  </div>
                  <div v-else>
                    <div><span style="font-weight: bold">info</span></div>
                    <div><span style="white-space: pre-wrap;">{{ item.info | errorFormat }}</span></div>
                  </div>
                </el-collapse-item>
              </el-collapse>
            </el-step>
          </el-steps>
        </div>
      </el-scrollbar>
      <div style="float:right" v-if="!conditionLoading">
        <el-button size="small" v-if="log.status === 'Failed'" @click="onRetry()">{{ $t("commons.button.retry")
        }}</el-button>
        <el-button size="small" v-if="log.status !== 'NotReady'" @click="goForLogs()">{{ $t("commons.button.log")
        }}</el-button>
      </div>
    </div>
  </div>
</template>

<script>
import { getTaskStatus, openLogger } from "@/api/task"

export default {
  name: "TaskLogs",
  props: {
    operation: String, // create-task || add-worker || terminal-node || terminal-cluster || not-ready
    taskName: String,
    nodeName: String,
  },
  data() {
    return {
      timer: null,
      timer2: null,
      conditionLoading: true,
      log: {
        status: "",
        preStatus: "",
        message: "",
        conditions: [],
      },
      activeName: 1,
      activeCollapse: 0,
      dialogHeight: "200px",
    }
  },
  methods: {
    loadStepIcon(status) {
      switch (status) {
        case "True":
          return "el-icon-check"
        case "False":
          return "el-icon-close"
        case "Unknown":
          return "el-icon-loading"
      }
    },
    goForLogs() {
      openLogger(this.taskName)
    },
    onRetry() {
      let preStatus = this.log.preStatus
      console.log('this.log :>> ', this.log);
      if (this.log.conditions.length !== 0) {
        this.log.conditions[this.log.conditions.length - 1].status = "Unknown"
      } else {
        this.conditionLoading = true
      }
      this.log.status = "Waiting"
      switch (this.operation) {
        // case "add-worker":
        //   this.$emit("retry", this.log.id, preStatus)
        //   break
        // case "terminal-node":
        //   this.log.status = "Terminating"
        //   this.log.preStatus = "Failed"
        //   this.$emit("retry", "", preStatus)
        //   break
        case "create-task":
          this.$emit("retry", preStatus)
          break
        // case "update-cluster":
        //   this.$emit("retry", preStatus)
        //   break
      }
    },
    getStatus() {
      this.dialogHeight = "330px"
      console.log('this.operation :>> ', this.operation);
      switch (this.operation) {
        case "create-task":
          getTaskStatus(this.taskName).then((data) => {
            if (data.conditions.length !== 0) {
              this.conditionLoading = false
            }
            this.handleResponse(data)
            this.dialogPolling()
          })
          break
        case "add-worker":
          // getNodeStatus(this.taskName, this.nodeName).then((data) => {
          //   this.log.id = data.id
          //   if (data.conditions.length !== 0) {
          //     this.conditionLoading = false
          //   }
          //   this.handleResponse(data)
          //   this.dialogPolling()
          // })
          break
        case "not-ready": {
          this.dialogHeight = "200px"
          getTaskStatus(this.taskName).then((data) => {
            this.conditionLoading = false
            if (data.status === "NotReady") {
              this.log = {
                status: "NotReady",
                message: data.message,
                conditions: [{ name: "CheckAPIStatus", formatMsgs: [{ name: this.taskName, info: data.message, type: "unFormat", failed: true }], status: "False", message: data.message }],
              }
            } else {
              this.$emit("cancle")
            }
          })
          break
        }
        case "terminal-node": {
          this.dialogHeight = "200px"
          this.conditionLoading = false
          this.log = {
            status: "Terminating",
            message: "",
            conditions: [{ name: "DeleteNode", status: "Unknown", message: "" }],
          }
          this.dialogPolling2()
        }
      }
    },
    // 拉取clusterStatus
    dialogPolling() {
      this.timer = setInterval(() => {
        if (this.log.conditions.length !== 0 || this.log.status === "Failed") {
          this.conditionLoading = false
        }
        let isConditionNotOK = true
        if (this.log.conditions.length !== 0) {
          let lastCondition = this.log.conditions[this.log.conditions.length - 1]
          isConditionNotOK = lastCondition.status !== "True" && lastCondition.status !== "False"
        } else {
          isConditionNotOK = false
        }
        if ((this.log.status !== "Running" && this.log.status !== "Failed") || isConditionNotOK) {
          if (this.operation == "add-worker") {
            // getNodeStatus(this.taskName, this.nodeName)
            //   .then((data) => {
            //     this.handleResponse(data)
            //   })
            //   .catch(() => {
            //     clearInterval(this.timer)
            //     this.timer = null
            //     this.$emit("cancle")
            //   })
          } else {
            getTaskStatus(this.taskName)
              .then((data) => {
                this.handleResponse(data)
              })
              .catch(() => {
                clearInterval(this.timer)
                this.timer = null
                this.$emit("cancle")
              })
          }
        } else {
          this.activeName = this.log.conditions.length + 1
        }
      }, 5000)
    },
    handleResponse(data) {
      console.log('data :>> ', data);
      this.activeName = data.conditions.length + 1
      this.log.id = data.id
      this.log.conditions = data.conditions
      if (this.log.status !== data.status) {
        this.log.status = data.status
      }
      this.log.message = data.message
      if (this.log.preStatus !== data.preStatus) {
        this.log.preStatus = data.preStatus
      }
      for (const condition of this.log.conditions) {
        condition.formatMsgs = []
        if (condition.status === "False") {
          condition.formatMsgs = this.handleErrMsg(condition.message)
        }
      }
    },
    // 错误处理
    handleErrMsg(str) {
      let formatMsgs = []
      if (!this.isJson(str)) {
        return [{ name: "Error Message", info: str, failed: false, type: "unFormat" }]
      }
      var json1 = JSON.parse(str)
      for (const key in json1) {
        var itemMsg = { name: "", info: {}, failed: false }
        itemMsg.name = key
        if (this.isJson(json1[key])) {
          var json2 = JSON.parse(json1[key])
          console.log('json2 :>> ', json2);
          itemMsg.info = json2
          if (itemMsg.info.msg) {
            itemMsg.info.msg = itemMsg.info.msg.replace(/\t/g, "").trim()
          }
          if (itemMsg.info.stdout) {
            itemMsg.info.stdout = itemMsg.info.stdout.replace(/\t/g, "").trim()
          }
          if (itemMsg.info.stderr) {
            itemMsg.info.stderr = itemMsg.info.stderr.replace(/\t/g, "").trim()
          }
          if (itemMsg.info.unreachable) {
            itemMsg.failed = true
          } else {
            itemMsg.failed = json2.failed
          }
        } else {
          itemMsg.type = "unFormat"
          itemMsg.info = JSON.stringify(json1[key]) // 解决错误信息非字符串产生格式化问题
          console.log('itemMsg :>> ', itemMsg);
        }
        if (itemMsg.info.length !== 0) {
          formatMsgs.push(itemMsg)
        }
      }
      return formatMsgs
    },
    isJson(str) {
      try {
        if (typeof JSON.parse(str) === "object") {
          return true
        }
      } catch {
        return false
      }
    },
  },
  created() {
    this.getStatus()
  },
  destroyed() {
    clearInterval(this.timer)
    clearInterval(this.timer2)
    this.timer = null
    this.timer2 = null
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
