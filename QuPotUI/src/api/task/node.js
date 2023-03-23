import { get } from "@/plugins/request"

const taskUrl = "/api/runtime/task"

export function listNodeInTask(taskName, currentPage, pageSize, isPolling) {
  return get(`${taskUrl}/nodes/${taskName}/?pageNum=${currentPage}&pageSize=${pageSize}&isPolling=${isPolling}`)
}

