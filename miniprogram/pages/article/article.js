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
    if (options.id) {
      this.loadDetail(options.id)
      return
    }
    this.loadList()
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

    wx.navigateTo({
      url: `/pages/article/article?id=${id}`,
    })
  },
})
