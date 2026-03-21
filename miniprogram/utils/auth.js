/**
 * 用户认证工具
 * 封装微信登录流程：wx.login → 后端 /user/login → 存储 token
 */
const { API_BASE, STORAGE_KEYS } = require('./constant')
const { post } = require('./request')

/**
 * 静默登录
 * 调用 wx.login() 获取临时 code，换取后端 JWT token
 * 成功后将 token 和 userInfo 持久化到 Storage 与 App.globalData
 *
 * @returns {Promise<{token: string, userInfo: object}>}
 */
function login() {
  return new Promise((resolve, reject) => {
    wx.login({
      success(loginRes) {
        if (!loginRes.code) {
          console.error('[Auth] wx.login 未返回 code', loginRes)
          reject(new Error('wx.login 失败'))
          return
        }

        post('/user/login', { code: loginRes.code })
          .then(res => {
            const { token, userInfo } = res.data

            // 持久化到 Storage
            wx.setStorageSync(STORAGE_KEYS.TOKEN, token)
            wx.setStorageSync(STORAGE_KEYS.USER_INFO, userInfo)

            // 同步到全局数据
            const app = getApp()
            if (app) {
              app.globalData.token = token
              app.globalData.userInfo = userInfo
            }

            console.log('[Auth] 登录成功，用户 ID:', userInfo.id)
            resolve({ token, userInfo })
          })
          .catch(err => {
            console.error('[Auth] 后端登录接口失败', err)
            reject(err)
          })
      },
      fail(err) {
        console.error('[Auth] wx.login 调用失败', err)
        reject(err)
      },
    })
  })
}

/**
 * 清除登录状态（退出登录时调用）
 */
function logout() {
  wx.removeStorageSync(STORAGE_KEYS.TOKEN)
  wx.removeStorageSync(STORAGE_KEYS.USER_INFO)

  const app = getApp()
  if (app) {
    app.globalData.token = null
    app.globalData.userInfo = null
  }
}

/**
 * 检查本地 token 是否存在（不校验服务端有效性）
 * @returns {boolean}
 */
function isLoggedIn() {
  return !!wx.getStorageSync(STORAGE_KEYS.TOKEN)
}

module.exports = { login, logout, isLoggedIn }
