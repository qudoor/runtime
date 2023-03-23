import {get, patch, post, del} from "@/plugins/request"


const settingUrl = "/api/runtime"

// Settings
// export function getSetting(tabName) {
//   return get(`${settingUrl}/${tabName}`)
// }
// export function check(tabName,data){
//   return post(`${settingUrl}/check/${tabName}`,data)
// }

// export function createSetting(data) {
//   return post(settingUrl,data)
// }

// Registry
export function listRegistry(currentPage, pageSize) {
  return get(`${settingUrl}/registry/?pageNum=${currentPage}&pageSize=${pageSize}`)
}

export function listRegistryAll() {
  return get(`${settingUrl}/registry/`)
}

export function createRegistry(data) {
  return post(`${settingUrl}/registry/`,data)
}

export function changePassword(data) {
  return post(`${settingUrl}/registry/change/password/`,data)
}

export function updateRegistry(arch, data) {
  return patch(`${settingUrl}/registry/${arch}/`,data)
}

export function testConnection(data) {
  return post(`${settingUrl}/registry/check/conn/`, data)
}

export function searchRegistry(currentPage, pageSize, conditions) {
  return post(`${settingUrl}/registry/search/?pageNum=${currentPage}&pageSize=${pageSize}`, conditions)
}

export function getRegistry(id) {
  return get(`${settingUrl}/registry/${id}/`)
}

export function deleteRegistry(id) {
  return del(`${settingUrl}/registry/${id}/`)
}

// ko
export function getKo(id) {
  return get(`${settingUrl}/ko/${id}/`)
}
export function searchKo() {
  return get(`${settingUrl}/ko/`)
}

export function deleteKo(id) {
  return del(`${settingUrl}/ko/${id}`)
}

export function checkKoAuth(data) {
  return post(`${settingUrl}/ko/check/conn/`, data)
}

export function createKo(data) {
  return post(`${settingUrl}/ko/`, data)
}

export function updateKo(id, data) {
  return patch(`${settingUrl}/ko/${id}/`, data)
}
