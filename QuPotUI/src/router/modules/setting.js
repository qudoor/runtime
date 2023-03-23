import Layout from "@/business/app-layout/horizontal-layout";

const SystemSetting = {
  path: '/setting',
  sort: 12,
  component: Layout,
  name: 'systemSetting',
  redirect: to => {
    return {
      name: 'setting',
      params: to.params,
    }
  },
  meta: {
    title: "系统设置",
    icon: 'iconfont iconxitongshezhi',
    activeMenu: "/setting/setting",
  },
  children: [
    {
      path: 'setting',
      component: () => import('@/business/runtime-system-setting/index'),
      name: "setting",
      hidden: true,
      props: true,
      redirect: to => {
        return {
          name: 'Registry',
          params: to.params,
        }
      },
      children: [
        {
          path: "registry",
          name: "Registry",
          hidden: true,
          props: true,
          component: () => import('@/business/runtime-system-setting/registry'),
          meta: {
            activeMenu: "/setting/setting",
          },
        },
        {
          path: "credential",
          name: "Credential",
          hidden: true,
          props: true,
          component: () => import('@/business/runtime-system-setting/credential'),
          meta: {
            activeMenu: "/setting/setting",
          }
        },
        {
          path: "ko",
          name: "Ko",
          hidden: true,
          props: true,
          component: () => import('@/business/runtime-system-setting/ko'),
          meta: {
            activeMenu: "/setting/setting",
          }
        },
      ],
    },
    {
      name: "RegistryCreate",
      path: "registry/create",
      hidden: true,
      component: () => import('@/business/runtime-system-setting/registry/create'),
      meta: {
        activeMenu: "/setting/setting",
      },
    },
    {
      name: "RegistryEdit",
      path: "registry/edit/:id",
      props: true,
      hidden: true,
      component: () => import('@/business/runtime-system-setting/registry/edit'),
      meta: {
        activeMenu: "/setting/setting",
      }
    },
    {
      name: "RuntimeCredentialCreate",
      path: "runtimecredential/create",
      props: true,
      hidden: true,
      component: () => import('@/business/runtime-system-setting/credential/create'),
      meta: {
        activeMenu: "/setting/setting",
      },
    },
    {
      name: "RuntimeCredentialEdit",
      path: "runtimecredential/edit/:name",
      props: true,
      hidden: true,
      component: () => import('@/business/runtime-system-setting/credential/edit'),
      meta: {
        activeMenu: "/setting/setting",
      }
    },
    {
      name: "KoCreate",
      path: "ko/create",
      hidden: true,
      component: () => import('@/business/runtime-system-setting/ko/create'),
      meta: {
        activeMenu: "/setting/setting",
      },
    },
    {
      name: "KoEdit",
      path: "ko/edit/:id",
      props: true,
      hidden: true,
      component: () => import('@/business/runtime-system-setting/ko/create'),
      meta: {
        activeMenu: "/setting/setting",
      }
    },
  ]
}
export default SystemSetting
