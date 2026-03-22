const { get } = require('../../utils/request')
const { STORAGE_KEYS } = require('../../utils/constant')

Page({
  data: {
    itemId: null,
    loading: true,
    item: null,
    imageResult: null,
    errorMessage: '',
  },

  onLoad(options) {
    const mode = options.mode || 'detail'
    if (mode === 'image') {
      this.loadImageResult()
      return
    }

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

  formatImageResult(imageResult) {
    if (!imageResult) {
      return null
    }

    return {
      ...imageResult,
      confidenceText: `${((imageResult.confidence || 0) * 100).toFixed(1)}%`,
      top3: (imageResult.top3 || []).map(item => ({
        ...item,
        confidenceText: `${((item.confidence || 0) * 100).toFixed(1)}%`,
      })),
    }
  },

  loadImageResult() {
    const storedResult = wx.getStorageSync(STORAGE_KEYS.LAST_IMAGE_RESULT)
    if (!storedResult) {
      this.setData({
        loading: false,
        errorMessage: '未找到最近一次图像识别结果，请重新拍照',
      })
      return
    }

    const imageResult = this.formatImageResult(storedResult)
    wx.removeStorageSync(STORAGE_KEYS.LAST_IMAGE_RESULT)

    const itemId = imageResult.itemId || ''
    this.setData({
      imageResult,
      itemId,
      item: imageResult.matchedItem || null,
      loading: !!itemId,
      errorMessage: '',
    })

    if (!itemId) {
      this.setData({ loading: false })
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
    const itemId = this.data.itemId || (this.data.item && this.data.item.id)
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

  goSearchSuggestion() {
    const { imageResult, item } = this.data
    const keyword = encodeURIComponent(
      (item && item.name) ||
      (imageResult && imageResult.labelZh) ||
      (imageResult && imageResult.category) ||
      ''
    )
    wx.navigateTo({
      url: `/pages/search/search?keyword=${keyword}`,
    })
  },

  goBackToCamera() {
    wx.redirectTo({
      url: '/pages/camera/camera',
    })
  },
})
