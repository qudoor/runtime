import { get, post } from "@/plugins/request"

const appStoreBaseUrl = "/api/appstore/";


export function getAppList(cluster_name) {
  return get(appStoreBaseUrl + cluster_name + '/app_list/')
}

export function createApp(cluster_name, app_name, data) {
  return post(appStoreBaseUrl + cluster_name + '/create_app/' + app_name + "/", data)
}

