/**
 * 全局常量配置
 * 修改 BASE_URL 指向实际后端地址
 */

// 后端 API 基础地址
// 开发期：指向本机 Flask 服务（微信开发者工具需开启"不校验合法域名"）
// 生产期：替换为 https://your-domain.com
const BASE_URL = 'http://localhost:5000'

// API 版本前缀
const API_PREFIX = '/api/v1'

// 完整 API 地址
const API_BASE = BASE_URL + API_PREFIX

// 请求超时时间（毫秒）
const REQUEST_TIMEOUT = 15000

// Storage Key 常量
const STORAGE_KEYS = {
  TOKEN: 'access_token',
  USER_INFO: 'user_info',
}

// 垃圾分类颜色映射（与后端 category.code 对应）
const CATEGORY_COLORS = {
  recyclable: '#4CAF50',    // 可回收物 — 绿色
  hazardous: '#F44336',     // 有害垃圾 — 红色
  kitchen: '#FF9800',       // 厨余垃圾 — 橙色
  other: '#9E9E9E',         // 其他垃圾 — 灰色
}

module.exports = {
  BASE_URL,
  API_PREFIX,
  API_BASE,
  REQUEST_TIMEOUT,
  STORAGE_KEYS,
  CATEGORY_COLORS,
}
