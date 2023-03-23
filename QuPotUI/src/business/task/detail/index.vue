<template>
  <layout-content :header="$t('task.task_details') + '  -  ' + clusterName" :back-to="{ name: 'TaskList' }">
    <div v-loading="loading">
      <el-menu @select="search" router :default-active="$route.path" mode="horizontal">
        <el-menu-item :index="'/task/detail/'+name+'/overview'">{{$t('cluster.detail.tag.overview')}}</el-menu-item>
        <el-menu-item :index="'/task/detail/'+name+'/node'">{{$t('cluster.detail.tag.node')}}</el-menu-item>
      </el-menu>
      <br />
      <div>
        <router-view></router-view>
      </div>
    </div>
  </layout-content>
</template>

<script>
import LayoutContent from "@/components/layout/LayoutContent"
import { getTaskByName } from "@/api/task"

export default {
  name: "ClusterDetail",
  props: ["project", "name"],
  components: { LayoutContent },
  data() {
    return {
      hasLicense: null,
      arch: null,
      loading: false,
      clusterName: "",
    }
  },
  methods: {
    search() {
      this.loading = true
      getTaskByName(this.$route.params.name)
        .then((data) => {
          if (data.spec.architectures) {
            this.arch = data.spec.architectures
            this.loading = false
          }
        })
        .catch(() => {
          this.loading = false
        })
    },
  },
  mounted() {
    this.$store.dispatch("license/getLicense").then((data) => {
      this.hasLicense = data.status === "valid"
    })
    this.clusterName = this.$route.params.name
    this.search()
  },
}
</script>

<style scoped>
</style>
