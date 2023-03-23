// 根据实际需要修改
const getters = {
  sidebar: state => state.app.sidebar,
  // name: state => state['user-token'].name,
  username: state => state['user-token'].username,
  // language: state => state['user-token'].language,
  roles: state => state['user-token'].roles,
  permission_routes: state => state.permission.routes,
  // license: state => state.license,
  // theme: state => state.theme.theme,
}
export default getters
