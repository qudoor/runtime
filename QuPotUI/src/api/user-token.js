/* 前后端分离的登录方式 */
import { get, post } from "@/plugins/request"

const authUrl = "/api/auth/"

export function getCurrentUser() {
  return get(authUrl + "info/")
}

export function login(data) {
  return post(authUrl + 'login/', data)
}
