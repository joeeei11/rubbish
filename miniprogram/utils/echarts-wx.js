/**
 * 小程序环境适配版 ECharts
 * 标准 echarts npm 包依赖 DOM API（addEventListener 等），在小程序中会报错。
 * 本模块对 echarts 进行平台适配，使其可在微信小程序中正常运行。
 */
const echarts = require('../miniprogram_npm/echarts/index')

// echarts 5.3+ 平台 API 适配
if (typeof echarts.setPlatformAPI === 'function') {
  echarts.setPlatformAPI({
    createCanvas() {
      return wx.createOffscreenCanvas({ type: '2d' })
    },
  })
}

/**
 * 为 canvas 对象补齐小程序缺失的 DOM 方法
 * echarts ZRender 初始化时会调用 addEventListener / removeEventListener
 * @param {object} canvas - WxCanvas 或原生 canvas 实例
 */
function patchCanvasForEcharts(canvas) {
  if (!canvas.addEventListener) {
    canvas.addEventListener = function () {}
  }
  if (!canvas.removeEventListener) {
    canvas.removeEventListener = function () {}
  }
  if (!canvas.dispatchEvent) {
    canvas.dispatchEvent = function () {}
  }
  if (!canvas.style) {
    canvas.style = { cursor: 'default' }
  }
  if (!canvas.getBoundingClientRect) {
    canvas.getBoundingClientRect = function () {
      return { left: 0, top: 0, width: canvas.width || 0, height: canvas.height || 0 }
    }
  }
  return canvas
}

module.exports = { echarts, patchCanvasForEcharts }
