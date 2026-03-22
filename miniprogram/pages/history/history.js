const { get } = require('../../utils/request')
const { login } = require('../../utils/auth')

const TYPE_META = {
  image: { icon: '📷', text: '图片识别' },
  voice: { icon: '🎤', text: '语音查询' },
  text: { icon: '🔍', text: '文字搜索' },
}

Page({
  data: {
    loading: true,
    loginLoading: false,
    histories: [],
    emptyText: '暂无查询记录',
    needLogin: false,
  },

  onShow() {
    this.loadHistories()
  },

  formatHistories(items = []) {
    return items.map((item) => {
      const meta = TYPE_META[item.queryType] || TYPE_META.text
      const garbageItem = item.garbageItem || null
      const category = garbageItem ? garbageItem.category : null

      return {
        ...item,
        typeIcon: meta.icon,
        typeText: meta.text,
        categoryName: category ? category.name : '未匹配',
        categoryCode: category ? category.code : '',
        categoryColor: category ? category.color : '#CBD5E1',
        displayName: garbageItem ? garbageItem.name : (item.queryInput || '未识别内容'),
        displayDesc: garbageItem
          ? (garbageItem.reason || garbageItem.description || item.queryInput || '')
          : (item.queryInput || '暂无更多信息'),
        createdAtText: this.formatDate(item.createdAt),
      }
    })
  },

  formatDate(value) {
    if (!value) {
      return ''
    }

    const normalized = value.replace('T', ' ').slice(0, 16)
    return normalized
  },

  loadHistories() {
    this.setData({
      loading: true,
      needLogin: false,
    })

    get('/history', { page: 1, size: 20 })
      .then((data) => {
        const histories = this.formatHistories(data.list || [])
        this.setData({
          histories,
          emptyText: histories.length ? '' : '暂无查询记录，去试试拍照、语音或文字搜索吧',
        })
      })
      .catch((err) => {
        const code = err && err.code
        this.setData({
          histories: [],
          needLogin: code === 40101 || code === 40102,
          emptyText: code === 40101 || code === 40102
            ? '登录后可查看你的查询历史'
            : (err.message || '历史记录加载失败'),
        })
      })
      .finally(() => {
        this.setData({ loading: false })
      })
  },

  retryLogin() {
    if (this.data.loginLoading) {
      return
    }

    this.setData({ loginLoading: true })
    login()
      .then(() => {
        this.loadHistories()
      })
      .catch((err) => {
        wx.showToast({
          title: err.message || '登录失败',
          icon: 'none',
        })
      })
      .finally(() => {
        this.setData({ loginLoading: false })
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
