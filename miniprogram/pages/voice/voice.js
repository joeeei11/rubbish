/**
 * 语音查询页面
 * 利用微信键盘自带的语音输入功能，用户点击键盘麦克风按钮说话，
 * 识别结果自动填入输入框，确认后搜索垃圾分类。
 */
const { get } = require('../../utils/request')

Page({
  data: {
    keyword: '',
    searching: false,
    results: [],
    errorMessage: '',
    emptyText: '点击输入框，使用键盘上的麦克风按钮语音输入',
    inputFocus: false,
  },

  onLoad(options) {
    const keyword = decodeURIComponent(options.keyword || '')
    if (keyword) {
      this.setData({ keyword })
      this.doSearch(keyword)
    }
  },

  onShow() {
    // 自动聚焦输入框，弹出键盘
    this.setData({ inputFocus: true })
  },

  onInputChange(e) {
    this.setData({ keyword: e.detail.value })
  },

  onInputConfirm(e) {
    const keyword = (e.detail.value || '').trim()
    if (keyword) {
      this.doSearch(keyword)
    }
  },

  handleSearch() {
    const keyword = (this.data.keyword || '').trim()
    if (!keyword) {
      this.setData({ errorMessage: '请输入或说出垃圾名称' })
      return
    }
    this.doSearch(keyword)
  },

  doSearch(keyword) {
    this.setData({
      searching: true,
      errorMessage: '',
      results: [],
      emptyText: '搜索中...',
    })

    get('/classify/search', { q: keyword }, false)
      .then((data) => {
        const results = data.list || []
        this.setData({
          results,
          emptyText: results.length ? '' : '没有找到匹配结果，试试换个说法',
        })
      })
      .catch((err) => {
        this.setData({
          results: [],
          errorMessage: err.message || '搜索失败，请重试',
        })
      })
      .finally(() => {
        this.setData({ searching: false })
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

  clearInput() {
    this.setData({
      keyword: '',
      results: [],
      errorMessage: '',
      emptyText: '点击输入框，使用键盘上的麦克风按钮语音输入',
    })
  },
})
