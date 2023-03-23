import { get, patch, post, del } from "@/plugins/request"

const userUrl = "/api/auth/user"


export function updateUser(username, data) {
  return patch(`${userUrl}/${username}/`, data)
}

export function listUsers(currentPage, pageSize) {
  return get(`${userUrl}/?pageNum=${currentPage}&pageSize=${pageSize}`)
}

export function createUser(data) {
  return post(userUrl + '/', data)
}

export function getUser(username) {
  return get(`${userUrl}/${username}/`)
}

export function deleteUser(username) {
  return del(`${userUrl}/${username}/`)
}
