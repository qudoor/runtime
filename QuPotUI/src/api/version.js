import { get } from "@/plugins/request"

export function getVersion() {
  return get('/ui/version.json?_=' + Math.random())
}
