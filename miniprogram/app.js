// app.js — 小程序全局逻辑
const { STORAGE_KEYS } = require('./utils/constant')
const { login } = require('./utils/auth')

App({
  globalData: {
    userInfo: null,
    token: null,
  },

  onLaunch() {
    // 从 Storage 恢复登录状态
    const token = wx.getStorageSync(STORAGE_KEYS.TOKEN)
    const userInfo = wx.getStorageSync(STORAGE_KEYS.USER_INFO)
    if (token) {
      this.globalData.token = token
      this.globalData.userInfo = userInfo
    }

    // 静默登录（刷新 token，失败不阻断页面加载）
    login().catch(err => {
      console.warn('[App] 静默登录失败，用户可在使用时手动触发登录', err)
    })
  },
})
