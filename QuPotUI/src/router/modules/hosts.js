import Layout from "@/business/app-layout/horizontal-layout";

const Host = {
  sort: 2,
  path: '/hosts',
  component: Layout,
  name: 'Host',
  meta: {
    title: "route.host",
    icon: 'iconfont iconhost',
  },
  children: [
    {
      path: "list",
      component: () => import("@/business/hosts"),
      name: "HostList",
      meta: {
        title: "runtime_host.host",
      }
    },
    {
      path: "hostCreate",
      hidden: true,
      name: "HostCreate",
      component: () => import('@/business/hosts/create'),
      meta: {
        activeMenu: "/hosts/list",
      },
    },
    {
      path: "editHost/:name",
      props: true,
      hidden: true,
      name: "HostEdit",
      component: () => import('@/business/hosts/edit'),
      meta: {
        activeMenu: "/hosts/list",
      },
    },
  ]
}
export default Host
