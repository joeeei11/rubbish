const { get } = require('../../utils/request')

Page({
  data: {
    itemId: null,
    graphData: null,
    loading: true,
    errorMessage: '',
  },

  onLoad(options) {
    const itemId = options.itemId || ''
    this.setData({ itemId })

    if (!itemId) {
      this.setData({
        loading: false,
        errorMessage: '请从结果页进入知识图谱',
      })
      return
    }

    this.fetchGraph(itemId)
  },

  fetchGraph(itemId) {
    this.setData({
      loading: true,
      errorMessage: '',
    })

    get('/knowledge/graph', { item_id: itemId }, false)
      .then(data => {
        this.setData({
          itemId,
          graphData: data,
        })
      })
      .catch(err => {
        this.setData({
          graphData: null,
          errorMessage: err.message || '图谱加载失败',
        })
      })
      .finally(() => {
        this.setData({ loading: false })
      })
  },

  handleNodeTap(event) {
    const { itemId } = event.detail
    if (!itemId || Number(itemId) === Number(this.data.itemId)) {
      return
    }
    this.fetchGraph(itemId)
  },
})
