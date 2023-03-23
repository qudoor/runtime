import {get} from "@/plugins/request"

export function systemQuery(page, size, conditions) {
  return get(`/api/tracking/record/?pageNum=${page}&pageSize=${size}`, conditions)
}
