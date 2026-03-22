const { get } = require('../../utils/request')

Page({
  data: {
    keyword: '',
    loading: false,
    searched: false,
    items: [],
    emptyText: '输入垃圾名称，开始搜索',
  },

  onLoad(options) {
    const keyword = decodeURIComponent(options.keyword || '').trim()
    if (!keyword) {
      return
    }

    this.setData({ keyword })
    this.fetchSearchResult(keyword)
  },

  onUnload() {
    if (this.searchTimer) {
      clearTimeout(this.searchTimer)
    }
  },

  handleInput(event) {
    const keyword = (event.detail.value || '').trim()
    this.setData({ keyword })

    if (this.searchTimer) {
      clearTimeout(this.searchTimer)
    }

    if (!keyword) {
      this.setData({
        searched: false,
        items: [],
        emptyText: '输入垃圾名称，开始搜索',
      })
      return
    }

    this.searchTimer = setTimeout(() => {
      this.fetchSearchResult(keyword)
    }, 300)
  },

  fetchSearchResult(keyword) {
    this.setData({
      loading: true,
      searched: true,
    })

    get('/classify/search', { q: keyword, page: 1, size: 20 }, false)
      .then(data => {
        this.setData({
          items: data.list || [],
          emptyText: (data.list || []).length ? '' : '没有找到匹配结果，换个关键词试试',
        })
      })
      .catch(err => {
        this.setData({
          items: [],
          emptyText: err.message || '搜索失败，请稍后再试',
        })
      })
      .finally(() => {
        this.setData({ loading: false })
      })
  },

  goDetail(event) {
    const { id } = event.currentTarget.dataset
    if (!id) {
      return
    }

    wx.navigateTo({
      url: `/pages/result/result?itemId=${id}`,
    })
  },
})
