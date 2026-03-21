const { get } = require('../../utils/request')

Page({
  data: {
    itemId: null,
    loading: true,
    item: null,
    errorMessage: '',
  },

  onLoad(options) {
    const itemId = options.itemId || ''
    this.setData({ itemId })

    if (!itemId) {
      this.setData({
        loading: false,
        errorMessage: '缺少物品编号，无法加载结果',
      })
      return
    }

    this.fetchDetail(itemId)
  },

  fetchDetail(itemId) {
    this.setData({
      loading: true,
      errorMessage: '',
    })

    get(`/garbage/${itemId}`, {}, false)
      .then(data => {
        this.setData({ item: data })
      })
      .catch(err => {
        this.setData({
          item: null,
          errorMessage: err.message || '加载失败，请稍后重试',
        })
      })
      .finally(() => {
        this.setData({ loading: false })
      })
  },

  goKnowledge() {
    const { itemId } = this.data
    if (!itemId) {
      return
    }
    wx.navigateTo({
      url: `/pages/knowledge/knowledge?itemId=${itemId}`,
    })
  },

  goRelatedDetail(event) {
    const { id } = event.currentTarget.dataset
    if (!id) {
      return
    }
    wx.redirectTo({
      url: `/pages/result/result?itemId=${id}`,
    })
  },
})
