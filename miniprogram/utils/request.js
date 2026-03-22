/**
 * wx.request 封装
 * 统一附加 Authorization 头，返回 Promise，统一处理业务错误码
 */
const { API_BASE, REQUEST_TIMEOUT, STORAGE_KEYS } = require('./constant')

/**
 * 发起请求
 * @param {object} options - 请求配置
 * @param {string} options.url       - 接口路径，如 /health（会自动拼接 API_BASE）
 * @param {string} [options.method]  - 请求方法，默认 GET
 * @param {object} [options.data]    - 请求体 / 查询参数
 * @param {boolean} [options.auth]   - 是否附加 JWT，默认 true
 * @returns {Promise<object>}         - 解析后的响应 data 字段
 */
function request(options) {
  const {
    url,
    method = 'GET',
    data = {},
    auth = true,
  } = options

  const header = {
    'Content-Type': 'application/json',
  }

  // 自动附加 JWT Token
  if (auth) {
    const token = wx.getStorageSync(STORAGE_KEYS.TOKEN)
    if (token) {
      header['Authorization'] = `Bearer ${token}`
    }
  }

  return new Promise((resolve, reject) => {
    wx.request({
      url: API_BASE + url,
      method,
      data,
      header,
      timeout: REQUEST_TIMEOUT,
      success(res) {
        const body = res.data
        if (body && body.code === 200) {
          resolve(body.data)
        } else {
          // 业务错误：token 失效时清除本地 token
          if (body && (body.code === 40101 || body.code === 40102)) {
            wx.removeStorageSync(STORAGE_KEYS.TOKEN)
            wx.removeStorageSync(STORAGE_KEYS.USER_INFO)
          }
          reject(body || { code: -1, message: '请求失败' })
        }
      },
      fail(err) {
        reject({ code: -2, message: '网络异常，请检查连接', raw: err })
      },
    })
  })
}

/**
 * GET 请求快捷方式
 */
function get(url, data = {}, auth = true) {
  return request({ url, method: 'GET', data, auth })
}

/**
 * POST 请求快捷方式
 */
function post(url, data = {}, auth = true) {
  return request({ url, method: 'POST', data, auth })
}

/**
 * 文件上传（图片识别）
 * @param {string} filePath - 本地图片路径
 * @returns {Promise<object>}
 */
function uploadImage(filePath) {
  const token = wx.getStorageSync(STORAGE_KEYS.TOKEN)
  const header = token ? { Authorization: `Bearer ${token}` } : {}

  return new Promise((resolve, reject) => {
    wx.uploadFile({
      url: API_BASE + '/classify/image',
      filePath,
      name: 'file',
      header,
      timeout: REQUEST_TIMEOUT,
      success(res) {
        try {
          const body = JSON.parse(res.data)
          if (body && body.code === 200) {
            resolve(body.data)
          } else {
            reject(body || { code: -1, message: '上传失败' })
          }
        } catch (e) {
          reject({ code: -3, message: '响应解析失败' })
        }
      },
      fail(err) {
        reject({ code: -2, message: '上传失败，请检查网络', raw: err })
      },
    })
  })
}

/**
 * 文件上传（语音识别）
 * @param {string} filePath - 本地音频路径
 * @returns {Promise<object>}
 */
function uploadAudio(filePath) {
  const token = wx.getStorageSync(STORAGE_KEYS.TOKEN)
  const header = token ? { Authorization: `Bearer ${token}` } : {}

  return new Promise((resolve, reject) => {
    wx.uploadFile({
      url: API_BASE + '/classify/voice',
      filePath,
      name: 'audio',
      header,
      timeout: REQUEST_TIMEOUT,
      success(res) {
        try {
          const body = JSON.parse(res.data)
          if (body && body.code === 200) {
            resolve(body.data)
          } else {
            reject(body || { code: -1, message: '上传失败' })
          }
        } catch (e) {
          reject({ code: -3, message: '响应解析失败' })
        }
      },
      fail(err) {
        reject({ code: -2, message: '上传失败，请检查网络', raw: err })
      },
    })
  })
}

module.exports = { request, get, post, uploadImage, uploadAudio }
