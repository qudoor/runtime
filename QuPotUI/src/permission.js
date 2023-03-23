import router from './router'
import store from './store'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

NProgress.configure({ showSpinner: false }) // NProgress Configuration

const whiteList = ['/login'] // no redirect whitelist

const generateRoutes = async (to, from, next) => {
  const isLogin = store.getters.username
  if (isLogin) {
    next()
  } else {
    try {
      const res = await store.dispatch('user-token/getCurrentUser')
      const roles = res.isSuperuser ? ['ADMIN'] : []
      console.log('generate routes roles :>> ', roles);
      const accessRoutes = await store.dispatch('permission/generateRoutes', { roles })
      router.addRoutes(accessRoutes)
      next({ ...to, replace: true })
    } catch (error) {
      await store.dispatch('user-token/logout')
      next(`/login?redirect=${to.path}`)
      NProgress.done()
    }
  }
}

// 路由前置钩子，根据实际需求修改
router.beforeEach(async (to, from, next) => {
  NProgress.start()

  const isLogin = await store.dispatch('user-token/isLogin')

  console.log('beforeEach isLogin :>> ', isLogin);

  if (isLogin) {
    if (to.path === '/login') {
      next({ path: '/' })
      NProgress.done()
    } else {
      await generateRoutes(to, from, next)
    }
  } else {
    /* has not login*/
    if (whiteList.indexOf(to.path) !== -1) {
      // in the free login whitelist, go directly
      next()
    } else {
      // other pages that do not have permission to access are redirected to the login page.
      next(`/login?redirect=${to.path}`)
      NProgress.done()
    }
  }
})

router.afterEach(() => {
  // finish progress bar
  NProgress.done()
})


// // TEMP:  no  login page
// const generateRoutes = async () => {
//   const license = licenses.valid
//   const roles = ['admin']
//   const accessRoutes = await store.dispatch('permission/generateRoutes', {roles})
//   router.addRoutes(accessRoutes)
// }

// generateRoutes()