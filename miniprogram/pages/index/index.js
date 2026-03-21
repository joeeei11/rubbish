// pages/index/index.js — 首页逻辑
const { get } = require('../../utils/request')

Page({
  onLoad() {
    // 验证后端连通性（Phase 1 联调用）
    get('/health', {}, false)
      .then(data => {
        console.log('[健康检查] 后端连通，版本：', data.version)
      })
      .catch(err => {
        console.warn('[健康检查] 后端不可达：', err.message)
      })
  },

  goCamera() {
    wx.navigateTo({ url: '/pages/camera/camera' })
  },
  goVoice() {
    wx.navigateTo({ url: '/pages/voice/voice' })
  },
  goSearch() {
    wx.navigateTo({ url: '/pages/search/search' })
  },
  goKnowledge() {
    wx.navigateTo({ url: '/pages/knowledge/knowledge' })
  },
})
