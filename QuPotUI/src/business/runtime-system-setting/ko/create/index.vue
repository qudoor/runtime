<template>
  <layout-content :header="title" :back-to="{ name: 'Ko' }">
    <el-row>
      <el-col :span="4"><br /></el-col>
      <el-col :span="12">
        <div class="grid-content bg-purple-light">
          <el-form ref="form" label-position="left" v-loading="loading" :model="form" :rules="rules"
            label-width="140px">
            <el-form-item :label="'名字'" prop="name">
              <!-- <el-select style="width: 100%" v-model="form.name" :placeholder="$t('commons.validate.select')">
                <el-option v-for="item in nameOptions" :key="item.value" :value="item.value" :disabled="item.disabled">
                </el-option>
              </el-select> -->
              <el-input v-model="form.name" :disabled="true"></el-input>
            </el-form-item>
            <el-form-item :label="'链接'" prop="url">
              <el-input @input="attachable = false" @blur="attachable = false" v-model="form.url"
                :placeholder="'http://qupot.queco.cn/'"></el-input>
            </el-form-item>
            <el-form-item style="width: 100%" :label="$t('login.username')" prop="username">
              <el-input @input="attachable = false" @blur="attachable = false" v-model="form.username"
                :placeholder="'admin'"></el-input>
            </el-form-item>
            <el-form-item :label="$t('setting.password')" prop="password">
              <el-input @input="attachable = false" @blur="attachable = false" v-model="form.password" type="password"
                show-password></el-input>
            </el-form-item>
            <div style="float: right">
              <el-form-item>
                <el-button @click="onCancel()">{{ $t('commons.button.cancel') }}</el-button>
                <el-button v-if="!attachable" @click="checkKoAuth">{{
                  $t("commons.button.test_connection")
                }}</el-button>
                <el-button v-if="attachable" type="primary" @click="onSubmit" v-preventReClick>{{
                  $t('commons.button.submit')
                }}</el-button>
              </el-form-item>
            </div>
          </el-form>
        </div>
      </el-col>
      <el-col :span="4"><br /></el-col>
    </el-row>
  </layout-content>

</template>

<script>
import LayoutContent from "@/components/layout/LayoutContent"
import { createKo, checkKoAuth, updateKo, getKo } from "@/api/runtime-system-setting"
import _ from "lodash"
import Rule from "@/utils/rules"

export default {
  name: "RegistryCreate",
  components: { LayoutContent },
  props: ["dialogFormVisible"],
  data() {
    return {
      title: this.$t('commons.button.create'),
      id: '',
      isEdit: false,
      form: {
        name: "ko_url",
        url: "",
        username: "",
        password: "",
      },
      rules: {
        name: [Rule.RequiredRule],
        url: [Rule.RequiredRule],
        username: [Rule.RequiredRule],
        password: [Rule.RequiredRule],
      },
      // nameOptions: [{ value: "ko_url_dev" }, { value: "ko_url_prod" }, { value: "ko_url_test" }],
      protocolOptions: [{ value: "http" }, { value: "https" }],
      loading: false,
      attachable: false,
    }
  },
  methods: {
    onSubmit() {
      this.$refs.form.validate((valid) => {
        if (!valid) {
          return false
        }
        this.loading = true
        if (this.isEdit) {
          updateKo(this.id, this.form).then(() => {
            this.loading = false
            this.$message({
              type: "success",
              message: "更新成功"
            })
            this.$router.push({ name: "Ko" })
          })
        } else {
          createKo(this.form)
            .then(() => {
              this.loading = false
              this.$message({
                type: "success",
                message: this.$t("commons.msg.create_success"),
              })
              this.$router.push({ name: "Ko" })
            })
            .finally(() => {
              this.loading = false
            })
        }
      })
    },
    checkKoAuth() {
      this.$refs.form.validate((valid) => {
        if (!valid) {
          return false
        }
        let data = this.form
        checkKoAuth(data).then(() => {
          this.$message({
            type: "success",
            message: "连接性检测成功"
          })
          this.attachable = true
        })
      })
    },
    onCancel() {
      this.$router.push({ name: "Ko" })
    },
    setInitData() {
      if (!_.isNil(this.$route.params.id)) {
        this.id = this.$route.params.id
        this.title = this.$t('commons.button.edit')
        this.isEdit = true
        getKo(this.$route.params.id).then(data => {
          this.form.name = data.name
          this.form.url = data.url
          this.form.username = data.username
          this.form.password = ''
        })
      }
    },
  },
  computed: {
    validateCommit() {
      if (this.form.architecture && this.form.hostname && this.form.protocol) {
        return false
      } else {
        return true
      }
    },
  },
  created() {
    this.setInitData()
  }
}
</script>

<style scoped>

</style>
