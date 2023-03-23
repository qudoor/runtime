const IpEeg = /^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])$/
const PasswordPattern = /^(?=.*\d)(?=.*[a-zA-Z])[\da-zA-Z~!@#$%^&*]{8,30}$/
const NamePattern = /^[a-zA-Z0-9\u4e00-\u9fa5]{1}[a-zA-Z0-9_.\u4e00-\u9fa5-]{0,30}$/

// 命名中存在 "." 或 "/" 会导致后端路由解析失败，Django 后端路由正则 [^/.]+
// 不允许名字中包含 "." 或 "" 字符
const HostNamePattern = /^[a-zA-Z0-9\u4e00-\u9fa5]{1}[a-zA-Z0-9\u4e00-\u9fa5-]{0,30}$/

// 支持小写英文、数字和- 不能以数字开头
const ClusterNamePattern = /^[a-z]([-a-z0-9]{0,48})[a-z0-9]$/
// 支持小写英文、数字和-
const StorageNamePattern = /^[a-z0-9]([-a-z0-9]*[a-z0-9])?(\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*$/

const EsIndexPattern = /^[a-zA-Z]{1}[a-zA-Z0-9]{0,30}$/
const VmConfigPattern = /[a-zA-Z0-9]{1}[a-zA-Z0-9]{0,30}$/

const QuantumApp = {
  'qubox-demo': 'qubox-demo',
  'qufinance': 'qufinance',
  'qusprout': 'qusprout',
}


export default {
  IpEeg, PasswordPattern, HostNamePattern, NamePattern, EsIndexPattern, VmConfigPattern, ClusterNamePattern, StorageNamePattern, QuantumApp
}
