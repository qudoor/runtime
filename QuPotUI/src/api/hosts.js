import {get, post, del, patch} from "@/plugins/request"

const hostUrl= "/api/runtime/hosts";

export function createHost(data) {
  return post(hostUrl + '/', data)
}

export function deleteHost(name) {
  return del(`${hostUrl}/${name}/`)
}

export function listHosts(currentPage, pageSize) {
  if (!currentPage || !pageSize) {
    return get(`${hostUrl}/`)
  }
  return get(`${hostUrl}/?pageNum=${currentPage}&pageSize=${pageSize}`)
}

export function listHostsByQuproduct(quproduct) {
  return get(`${hostUrl}/quproduct/${quproduct}/`)
}

export function searchHosts(currentPage, pageSize,condition) {
  return post(`${hostUrl}/search/?pageNum=${currentPage}&pageSize=${pageSize}`,condition)
}

export function getHostByName(name) {
  return get(`${hostUrl}/${name}/`)
}

export function updateHost(host) {
  return patch(`${hostUrl}/${host.name}/`, host)
}

export function openTerminal(ip, port, credentialId) {
  window.open(`/ui/#/terminal?ip=${ip}&port=${port}&credentialId=${credentialId}`, "_blank", "height=865, width=800, top=0, left=0, toolbar=no, menubar=no, scrollbars=no, resizable=yes,location=no, status=no")
}

export function syncHosts(hosts) {
  const itemUrl = `${hostUrl}/sync/`
  return post(itemUrl, hosts)
}
