<template>
  <layout-content :header="$t('commons.button.edit')" :back-to="{ name: 'Credential' }">
    <el-row>
      <el-col :span="4"><br /></el-col>
      <el-col :span="10">
        <div class="grid-content bg-purple-light">
          <el-form ref="form" v-loading="loading" label-position="left" :model="form" label-width="80px" :rules="rules">
            <el-form-item :label="$t('credential.name')" prop="name">
              <el-input v-model="form.name" disabled></el-input>
              <span></span>
            </el-form-item>
            <el-form-item :label="$t('credential.username')" prop="username">
              <el-input v-model="form.username"></el-input>
            </el-form-item>
            <el-form-item :label="$t('credential.type')">
              <el-radio-group v-model="form.type">
                <el-radio label="password">{{ $t('credential.password') }}</el-radio>
                <el-radio label="privateKey">{{ $t('credential.privateKey') }}</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item v-if="form.type === 'password'" :label="$t('credential.password')" prop="password">
              <el-input type="password" show-password :placeholder="$t('setting.helpInfo.inputPassword')"
                v-model="form.password"></el-input>
            </el-form-item>
            <el-form-item v-if="form.type === 'privateKey'" :label="$t('credential.privateKey')" prop="privateKey">
              <el-input type="textarea" v-model="form.privateKey"></el-input>
            </el-form-item>
            <div style="float: right">
              <el-form-item>
                <el-button @click="onCancel()">{{ $t('commons.button.cancel') }}</el-button>
                <el-button type="primary" @click="onSubmit" v-preventReClick>{{ $t('commons.button.submit') }}</el-button>
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
import LayoutContent from "@/components/layout/LayoutContent";
import { updateCredentials, getCredentialByName } from "@/api/credentials";
import Rule from "@/utils/rules"

export default {
  components: {
    LayoutContent
  },
  name: "RuntimeCredentialEdit",
  props: ["name"],
  data() {
    return {
      form: {
        name: '',
        username: '',
        type: '',
        password: '',
        privateKey: ''
      },
      formLabelWidth: '120px',
      loading: false,
      rules: {
        name: [Rule.NameRule],
        username: [Rule.RequiredRule],
        password: [Rule.RequiredRule],
        privateKey: [Rule.RequiredRule],
      }
    }
  },
  methods: {
    onSubmit() {
      this.$refs.form.validate((valid) => {
        if (!valid) {
          return false
        }
        this.loading = true

        this.loading = true
        updateCredentials(this.form.name, {
          id: this.form.id,
          name: this.form.name,
          username: this.form.username,
          password: this.form.password,
          privateKey: this.form.privateKey,
          type: this.form.type,
        }).then(() => {
          this.loading = false
          this.$message({
            type: 'success',
            message: `创建成功`
          });
          this.$router.push({ name: 'Credential' })
        }).finally(() => {
          this.loading = false
        })
      })
    },
    onCancel() {
      this.$router.push({ name: 'Credential' })
    },
  },
  created() {
    getCredentialByName(this.name).then(data => {
      this.form.name = data.name,
        this.form.username = data.username,
        this.form.type = data.type,
        this.form.id = data.id
    })
  }
}
</script>

<style scoped>

</style>
