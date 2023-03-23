import { login, getCurrentUser } from "@/api/user-token"
import { resetRouter } from "@/router"
import { getToken, setToken, removeToken } from "@/utils/token"
import { getLanguage, setLanguage } from "@/i18n"

const state = {
  // token: getToken(),
  token: "",
  username: "",
  language: getLanguage(),
  roles: []
}

const mutations = {
  SET_TOKEN: (state, token) => {
    state.token = token
  },
  SET_USERNAME: (state, username) => {
    state.username = username
  },
  SET_LANGUAGE: (state, language) => {
    state.language = language
    setLanguage(language)
  },
  SET_ROLES: (state, roles) => {
    state.roles = roles
  }
}

const actions = {
  login({ commit }, userInfo) {
    const { username, password, captchaId, code } = userInfo
    return new Promise((resolve, reject) => {
      login({ username: username.trim(), password: password, captchaId: captchaId, code: code }).then(response => {
        let token = response.token
        commit("SET_TOKEN", token)
        setToken(token)
        resolve(response)
      }).catch(error => {
        reject(error)
      })
    })
  },

  isLogin({ commit }) {
    return new Promise((resolve) => {
      let token = getToken()
      if (token) {
        commit("SET_TOKEN", token)
        resolve(true)
      } else {
        console.log('reject');
        resolve(false)
      }
    })
  },

  getCurrentUser({ commit }) {
    return new Promise((resolve, reject) => {
      getCurrentUser().then(response => {
        const { username, isSuperuser } = response
        commit("SET_USERNAME", username)
        const roles = isSuperuser ? ['ADMIN'] : []
        commit("SET_ROLES", roles)// 暂时没有角色
        // commit("SET_LANGUAGE", language)
        resolve(response)
      }).catch(error => {
        reject(error)
      })
    })
  },

  setLanguage({ commit }, language) {
    commit("SET_LANGUAGE", language)
  },

  logout({ commit }) {
    commit("SET_TOKEN", "")
    commit("SET_USERNAME", "")
    commit("SET_ROLES", [])
    removeToken()
    resetRouter()
  },
}

export default {
  namespaced: true,
  state,
  mutations,
  actions
}
