import {get, post} from "@/plugins/request"

const clusterUrl = "/api/ops/ko/clusters"

export function getClusterByName(clusterName) {
  return get(`${clusterUrl}/${clusterName}/`)
}

export function searchClusters(page, size, condition, isPolling) {
  return post(`${clusterUrl}/search/?pageNum=${page}&pageSize=${size}&isPolling=${isPolling}`, condition)
}
