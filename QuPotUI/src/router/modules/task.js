import Layout from "@/business/app-layout/horizontal-layout"

const Task = {
  path: "/task",
  sort: 1,
  component: Layout,
  name: "Task",
  // meta: {
  //   title: "route.cluster",
  //   icon: "iconfont iconcluster",
  // },
  children: [
    {
      path: "list",
      component: () => import("@/business/task"),
      name: "TaskList",
      meta: {
        icon: "iconfont iconcluster",
        title: "task.title",
      },
    },
    {
      path: "create",
      hidden: true,
      component: () => import("@/business/task/create"),
      name: "TaskCreate",
      meta: {
        activeMenu: "/task/list",
      },
    },
    {
      path: "upgrade/:name",
      props: true,
      hidden: true,
      component: () => import("@/business/task/upgrade"),
      name: "TaskUpgrade",
      meta: {
        activeMenu: "/task/list",
      },
    },
    {
      path: "detail/:name",
      props: true,
      hidden: true,
      component: () => import("@/business/task/detail/index"),
      name: "TaskDetail",
      meta: {
        activeMenu: "/task/list",
      },
      children: [
        {
          path: "overview",
          name: "TaskOverview",
          hidden: true,
          props: true,
          component: () => import("@/business/task/detail/overview"),
          meta: {
            activeMenu: "/task/list",
          }
        },
        {
          path: "node",
          name: "TaskNode",
          hidden: true,
          props: true,
          component: () => import("@/business/task/detail/node"),
          meta: {
            activeMenu: "/task/list",
          }
        },
      ]
    }
  ]
}
export default Task
