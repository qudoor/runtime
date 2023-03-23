import { patch } from "@/plugins/request"

export function changePassword(data) {
  return patch('/api/auth/change-password/', data)
}

export function resetPassword(username, data) {
  return patch("/api/auth/user/" + username + "/reset-password/",data)
}
