const { uploadAudio } = require('../../utils/request')

const RECORD_OPTIONS = {
  duration: 10000,
  sampleRate: 16000,
  numberOfChannels: 1,
  format: 'pcm',
}

const INITIAL_WAVE_BARS = [44, 68, 92, 68, 44]

Page({
  data: {
    recording: false,
    recognizing: false,
    recognizedText: '',
    results: [],
    errorMessage: '',
    emptyText: '按住按钮说出垃圾名称，识别结果会显示在这里',
    permissionDenied: false,
    waveBars: INITIAL_WAVE_BARS,
  },

  onLoad() {
    this.initRecorder()
    this.checkRecordPermission()
  },

  onUnload() {
    this.stopWaveAnimation()
    if (this.data.recording && this.recorderManager) {
      try {
        this.recorderManager.stop()
      } catch (e) {
        // 忽略页面销毁时的停止异常
      }
    }
  },

  initRecorder() {
    if (this.recorderManager) {
      return
    }

    const recorderManager = wx.getRecorderManager()
    this.recorderManager = recorderManager

    recorderManager.onStart(() => {
      this.setData({
        recording: true,
        recognizing: false,
        errorMessage: '',
        recognizedText: '',
        results: [],
        emptyText: '请保持说话清晰，松开后会立即识别',
      })
      this.startWaveAnimation()
    })

    recorderManager.onStop((res) => {
      this.stopWaveAnimation()
      this.setData({
        recording: false,
        waveBars: INITIAL_WAVE_BARS,
      })

      if (!res || !res.tempFilePath) {
        this.setData({
          errorMessage: '未获取到录音文件，请重试',
          emptyText: '录音未成功保存，请重新按住说话',
        })
        return
      }

      this.uploadRecordedAudio(res.tempFilePath)
    })

    recorderManager.onError(() => {
      this.stopWaveAnimation()
      this.setData({
        recording: false,
        recognizing: false,
        waveBars: INITIAL_WAVE_BARS,
        errorMessage: '录音失败，请检查权限后重试',
        emptyText: '录音失败后可改用文字搜索',
      })
    })
  },

  checkRecordPermission() {
    return new Promise((resolve) => {
      wx.getSetting({
        success: (res) => {
          const granted = !!(res.authSetting || {})['scope.record']
          this.setData({ permissionDenied: !granted && res.authSetting && res.authSetting['scope.record'] === false })
          resolve(granted)
        },
        fail: () => resolve(false),
      })
    })
  },

  ensureRecordPermission() {
    return new Promise((resolve) => {
      wx.getSetting({
        success: (res) => {
          const authSetting = res.authSetting || {}
          if (authSetting['scope.record'] === true) {
            this.setData({ permissionDenied: false, errorMessage: '' })
            resolve(true)
            return
          }

          if (authSetting['scope.record'] === false) {
            this.promptOpenSetting(resolve)
            return
          }

          wx.authorize({
            scope: 'scope.record',
            success: () => {
              this.setData({ permissionDenied: false, errorMessage: '' })
              resolve(true)
            },
            fail: () => {
              this.promptOpenSetting(resolve)
            },
          })
        },
        fail: () => {
          this.setData({
            permissionDenied: true,
            errorMessage: '无法检查录音权限，请稍后重试',
          })
          resolve(false)
        },
      })
    })
  },

  promptOpenSetting(resolve) {
    this.setData({
      permissionDenied: true,
      errorMessage: '未开启录音权限，暂时无法语音查询',
      emptyText: '可以先开启录音权限，或改用文字搜索',
    })

    wx.showModal({
      title: '需要录音权限',
      content: '开启录音权限后，才能使用语音查询垃圾分类。',
      confirmText: '去开启',
      success: (modalRes) => {
        if (!modalRes.confirm) {
          resolve(false)
          return
        }

        wx.openSetting({
          success: (settingRes) => {
            const granted = !!(settingRes.authSetting || {})['scope.record']
            this.setData({
              permissionDenied: !granted,
              errorMessage: granted ? '' : '未开启录音权限，暂时无法语音查询',
            })
            resolve(granted)
          },
          fail: () => resolve(false),
        })
      },
      fail: () => resolve(false),
    })
  },

  async handleRecordStart() {
    if (this.data.recording || this.data.recognizing) {
      return
    }

    const granted = await this.ensureRecordPermission()
    if (!granted || !this.recorderManager) {
      return
    }

    try {
      this.recorderManager.start(RECORD_OPTIONS)
    } catch (e) {
      this.setData({
        errorMessage: '启动录音失败，请重试',
      })
    }
  },

  handleRecordEnd() {
    if (!this.data.recording || !this.recorderManager) {
      return
    }

    try {
      this.recorderManager.stop()
    } catch (e) {
      this.setData({
        recording: false,
        errorMessage: '停止录音失败，请重试',
      })
    }
  },

  handleRecordCancel() {
    this.handleRecordEnd()
  },

  startWaveAnimation() {
    this.stopWaveAnimation()
    this.waveTimer = setInterval(() => {
      if (!this.data.recording) {
        return
      }

      this.setData({
        waveBars: INITIAL_WAVE_BARS.map((base) => {
          const delta = Math.round(Math.random() * 34) - 12
          return Math.max(28, base + delta)
        }),
      })
    }, 180)
  },

  stopWaveAnimation() {
    if (!this.waveTimer) {
      return
    }

    clearInterval(this.waveTimer)
    this.waveTimer = null
  },

  uploadRecordedAudio(filePath) {
    this.setData({
      recognizing: true,
      errorMessage: '',
      emptyText: '识别中，请稍候...',
    })

    uploadAudio(filePath)
      .then((data) => {
        const results = data.results || []
        this.setData({
          recognizedText: data.recognized_text || '',
          results,
          emptyText: results.length ? '' : '没有找到完全匹配的结果，可改用文字搜索补充关键词',
        })
      })
      .catch((err) => {
        this.setData({
          recognizedText: '',
          results: [],
          errorMessage: err.message || '语音识别失败，请重试或改用文字搜索',
          emptyText: '识别失败后可以切换到文字搜索继续查询',
        })
      })
      .finally(() => {
        this.setData({ recognizing: false })
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

  goSearch() {
    const keyword = encodeURIComponent(this.data.recognizedText || '')
    wx.navigateTo({
      url: `/pages/search/search?keyword=${keyword}`,
    })
  },

  openSettings() {
    wx.openSetting({
      success: (res) => {
        const granted = !!(res.authSetting || {})['scope.record']
        this.setData({
          permissionDenied: !granted,
          errorMessage: granted ? '' : '未开启录音权限，暂时无法语音查询',
        })
      },
    })
  },
})
