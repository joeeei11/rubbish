const { get } = require('../../utils/request')
const { STORAGE_KEYS } = require('../../utils/constant')

const GUIDE_CATEGORIES = [
  { code: 'recyclable', name: '可回收物', color: '#4CAF50', keyword: '矿泉水瓶' },
  { code: 'hazardous', name: '有害垃圾', color: '#F44336', keyword: '干电池' },
  { code: 'kitchen', name: '厨余垃圾', color: '#FF9800', keyword: '果皮' },
  { code: 'other', name: '其他垃圾', color: '#9E9E9E', keyword: '纸巾' },
]

Page({
  data: {
    greetingName: '同学',
    todayArticle: null,
    categories: GUIDE_CATEGORIES,
  },

  onLoad() {
    this.checkHealth()
    this.syncUserGreeting()
    this.loadTodayArticle()
  },

  onShow() {
    this.syncUserGreeting()
  },

  checkHealth() {
    get('/health', {}, false)
      .then(data => {
        console.log('[健康检查] 后端连通，版本：', data.version)
      })
      .catch(err => {
        console.warn('[健康检查] 后端不可达：', err.message)
      })
  },

  syncUserGreeting() {
    const app = getApp()
    const storedUser = wx.getStorageSync(STORAGE_KEYS.USER_INFO) || {}
    const userInfo = (app && app.globalData && app.globalData.userInfo) || storedUser
    const nickname = (userInfo && userInfo.nickname) || ''

    this.setData({
      greetingName: nickname || '同学',
    })
  },

  loadTodayArticle() {
    get('/articles', { page: 1, size: 1 }, false)
      .then(data => {
        const article = (data.list || [])[0] || null
        this.setData({ todayArticle: article })
      })
      .catch(() => {
        this.setData({ todayArticle: null })
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

  goHistory() {
    wx.navigateTo({ url: '/pages/history/history' })
  },

  openTodayArticle() {
    const article = this.data.todayArticle
    if (!article || !article.id) {
      wx.navigateTo({ url: '/pages/article/article' })
      return
    }

    wx.navigateTo({
      url: `/pages/article/article?id=${article.id}`,
    })
  },

  openCategoryGuide(event) {
    const { keyword } = event.currentTarget.dataset
    wx.navigateTo({
      url: `/pages/search/search?keyword=${encodeURIComponent(keyword || '')}`,
    })
  },
})
