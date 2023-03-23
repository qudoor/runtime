import { post } from "@/plugins/request"
import { licenses } from "../../mock/license"

const licenseUrl = "/api/v1/license"

export function getLicense() {
  return new Promise((resolve) => {
    resolve(licenses.valid)
  })
}

export function importLicense(data) {
  return post(licenseUrl, data)
}
