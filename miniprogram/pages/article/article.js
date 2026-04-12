const { get } = require('../../utils/request')

Page({
  data: {
    mode: 'list',
    loading: true,
    articles: [],
    article: null,
    errorMessage: '',
  },

  onLoad(options) {
    // TabBar 页不接受 navigateTo 传参，参数中的 id 实际不会生效
    // 真正的文章 id 由 onShow 通过 globalData.pendingArticleId 接收
    this.loadList()
  },

  onShow() {
    // 检查是否有待显示的文章（来自首页"今日科普"或列表点击）
    const app = getApp()
    const pendingId = app.globalData && app.globalData.pendingArticleId
    if (pendingId) {
      app.globalData.pendingArticleId = null
      this.loadDetail(pendingId)
      return
    }
    // 从详情返回列表时重置为列表模式
    if (this.data.mode === 'list' && !this.data.loading) {
      this.loadList()
    }
  },

  loadList() {
    this.setData({
      mode: 'list',
      loading: true,
      errorMessage: '',
    })

    get('/articles', { page: 1, size: 20 }, false)
      .then(data => {
        this.setData({
          articles: data.list || [],
        })
      })
      .catch(err => {
        this.setData({
          articles: [],
          errorMessage: err.message || '文章列表加载失败',
        })
      })
      .finally(() => {
        this.setData({ loading: false })
      })
  },

  loadDetail(id) {
    this.setData({
      mode: 'detail',
      loading: true,
      errorMessage: '',
    })

    get(`/articles/${id}`, {}, false)
      .then(data => {
        this.setData({
          article: data,
        })
      })
      .catch(err => {
        this.setData({
          article: null,
          errorMessage: err.message || '文章详情加载失败',
        })
      })
      .finally(() => {
        this.setData({ loading: false })
      })
  },

  openArticle(event) {
    const { id } = event.currentTarget.dataset
    if (!id) {
      return
    }
    // TabBar 页无法用 navigateTo 跳转自身，直接在当前页切换到详情模式
    this.loadDetail(id)
  },

  backToList() {
    this.loadList()
  },
})
