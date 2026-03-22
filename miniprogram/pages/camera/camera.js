const { uploadImage } = require('../../utils/request')
const { STORAGE_KEYS } = require('../../utils/constant')

const MAX_EDGE = 512

Page({
  data: {
    imagePath: '',
    uploading: false,
    errorMessage: '',
  },

  chooseFromCamera() {
    this.chooseImage(['camera'])
  },

  chooseFromAlbum() {
    this.chooseImage(['album'])
  },

  chooseImage(sourceType) {
    if (this.data.uploading) {
      return
    }

    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType,
      success: async (res) => {
        const file = (res.tempFiles || [])[0]
        const tempFilePath = file && file.tempFilePath
        if (!tempFilePath) {
          this.setData({ errorMessage: '未获取到可用图片，请重试' })
          return
        }

        this.setData({
          imagePath: tempFilePath,
          errorMessage: '',
        })

        await this.uploadSelectedImage(tempFilePath)
      },
      fail: (err) => {
        const errMsg = (err && err.errMsg) || ''
        if (errMsg.includes('cancel')) {
          return
        }
        this.setData({
          errorMessage: '选择图片失败，请稍后重试',
        })
      },
    })
  },

  resizeImage(filePath) {
    return new Promise((resolve, reject) => {
      wx.getImageInfo({
        src: filePath,
        success: (info) => {
          const maxSide = Math.max(info.width, info.height)
          const scale = maxSide > MAX_EDGE ? MAX_EDGE / maxSide : 1
          const targetWidth = Math.max(1, Math.round(info.width * scale))
          const targetHeight = Math.max(1, Math.round(info.height * scale))
          const ctx = wx.createCanvasContext('imageCanvas', this)

          ctx.clearRect(0, 0, targetWidth, targetHeight)
          ctx.drawImage(filePath, 0, 0, targetWidth, targetHeight)
          ctx.draw(false, () => {
            wx.canvasToTempFilePath({
              canvasId: 'imageCanvas',
              x: 0,
              y: 0,
              width: targetWidth,
              height: targetHeight,
              destWidth: targetWidth,
              destHeight: targetHeight,
              fileType: 'jpg',
              quality: 0.9,
              success: (result) => resolve(result.tempFilePath),
              fail: reject,
            }, this)
          })
        },
        fail: reject,
      })
    })
  },

  compressImage(filePath) {
    return new Promise((resolve) => {
      wx.compressImage({
        src: filePath,
        quality: 70,
        success: (res) => resolve(res.tempFilePath || filePath),
        fail: () => resolve(filePath),
      })
    })
  },

  async uploadSelectedImage(filePath) {
    this.setData({
      uploading: true,
      errorMessage: '',
    })
    wx.showLoading({
      title: '识别中',
      mask: true,
    })

    try {
      const resizedPath = await this.resizeImage(filePath)
      const compressedPath = await this.compressImage(resizedPath)
      const result = await uploadImage(compressedPath)

      result.localImagePath = compressedPath
      wx.setStorageSync(STORAGE_KEYS.LAST_IMAGE_RESULT, result)

      wx.navigateTo({
        url: '/pages/result/result?mode=image',
      })
    } catch (err) {
      this.setData({
        errorMessage: err.message || '识别失败，请稍后重试',
      })
    } finally {
      wx.hideLoading()
      this.setData({ uploading: false })
    }
  },
})
