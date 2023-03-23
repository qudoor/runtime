import { get, post, del } from "@/plugins/request"

const taskUrl = "/api/runtime/task"
// const clusterLoggerUrl = taskUrl + "/logger/{cluster_name}"
const taskLoggerUrl = taskUrl + "/logger/{task_name}"
// const clusterNodeLoggerUrl = "/api/v1/clusters/node/logger/{cluster_name}/{node_name}"
// const storageProvisionerLoggerUrl = "/api/v1/clusters/provisioner/log/{cluster_name}/{log_id}"


export function listTask() {
  return get(`${taskUrl}/quproduct/all/`)
}
// 通过架构 去 nexus 中获取量子产品
// return get(`${taskUrl}/quproduct/${arch}/`)

// export function getArchByQuproduct(quproduct) {
//   return get(`${taskUrl}/arch/${quproduct}/`)
// }

export function getDependentsByArchAndQuproduct(arch, quproduct) {
  // return post(`${taskUrl}/dependents/${quproduct}/`)
  return get(`${taskUrl}/dependents/${arch}/${quproduct}/`)
}


export function getTaskByName(clusterName) {
  return get(`${taskUrl}/${clusterName}/`)
}

export function getClusterByProject(projectNames) {
  return get(`${taskUrl}/name/${projectNames}`)
}

export function checkClusterNameExistence(clusterName) {
  return get(`${taskUrl}/existence/${clusterName}/`)
}

export function listClusters(page, size) {
  return get(`${taskUrl}?pageNum=${page}&pageSize=${size}`)
}

export function searchTasks(page, size, condition, isPolling) {
  return post(`${taskUrl}/search/?pageNum=${page}&pageSize=${size}&isPolling=${isPolling}`, condition)
}

export function listAllClusters() {
  // TODO: 分页, 如果不加分页，后端返回 projectName 为空字符串
  return post(`${taskUrl}/search?pageNum=${1}&pageSize=${100}`)
}

export function createTask(data) {
  return post(`${taskUrl}/`, data)
}

export function healthCheck(clusterName) {
  return get(`${taskUrl}/health/${clusterName}/`)
}

export function clusterRecover(clusterName, data) {
  return post(`${taskUrl}/recover/${clusterName}`, data)
}

export function deleteCluster(clusterName, force, uninstall) {
  return del(`${taskUrl}/${clusterName}/?force=${force}&uninstall=${uninstall}`)
}

export function importCluster(data) {
  return post(`${taskUrl}/import/`, data)
}

export function searchDeployments(data) {
  return post(`${taskUrl}/provisioner/deployment/`, data)
}

export function allClusters() {
  return get(`${taskUrl}`)
}

export function retryTask(taskName) {
  return post(`${taskUrl}/${taskName}/retry/`)
}

export function upgradeCluster(taskName, version) {
  let req = {
    taskName: taskName,
    version: version,
  }
  return post(`${taskUrl}/upgrade/`, req)
}

export function getTaskStatus(taskName) {
  return get(`${taskUrl}/status/${taskName}/`)
}

// export function getClusterNodeLog(clusterName, nodeName) {
//   return get(clusterNodeLoggerUrl.replace("{cluster_name}", clusterName).replace("{node_name}", nodeName))
// }

export function getTaskLog(taskName, logId) {
  if (logId !== undefined) {
    // return get(storageProvisionerLoggerUrl.replace("{task_name}", clusterName).replace("{log_id}", logId))
  } else {
    return get(taskLoggerUrl.replace("{task_name}", taskName) + '/')
  }
}

export function openLogger(taskName) {
  window.open(`/ui/#/logger?taskName=${taskName}`, "_blank", "height=865, width=800, top=0, left=0, toolbar=no, menubar=no, scrollbars=no, resizable=yes,location=no, status=no")
}

export function openLoggerWithID(taskName, logId) {
  window.open(`/ui/#/logger?taskName=${taskName}&logId=${logId}`, "_blank", "height=865, width=800, top=0, left=0, toolbar=no, menubar=no, scrollbars=no, resizable=yes,location=no, status=no")
}

// export function getSecret(clusterName) {
//   return get(`${taskUrl}/secret/${clusterName}`)
// }

// export function getClusterInfo(data) {
//   return post(taskUrl + "/load", data)
// }

export function handleGpu(clusterName, handle) {
  return post(`${taskUrl}/gpu/${clusterName}/${handle}`)
}

export function getGpuStatu(clusterName) {
  return get(`${taskUrl}/gpu/${clusterName}`)
}
