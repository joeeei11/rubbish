// app.js — 小程序全局逻辑
const { STORAGE_KEYS } = require('./utils/constant')

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
  },
})
