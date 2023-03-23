import Layout from "@/business/app-layout/horizontal-layout";

const QuantumAppStore = {
  sort: 3,
  path: '/quantum_app_store',
  component: Layout,
  name: 'QuantumAppStore',
  children: [
    {
      path: 'cluster_list',
      component: () => import('@/business/quantum-app-store'),
      name: "QuantumAppStoreClusterList",
      meta: {
        title: "量子应用市场",
        icon: 'iconfont iconhost',
      },
    },
    {
      path: ":cluster/list",
      name: "StoreQuantumAppList",
      hidden: true,
      props: true,
      component: () => import("@/business/quantum-app-store/List"),
      meta: {
        title: "量子应用市场",
        activeMenu: "/quantum_app_store/cluster_list",
      }
    },
  ]
}
export default QuantumAppStore
