const { echarts, patchCanvasForEcharts } = require('../../utils/echarts-wx')

function buildOption(graphData) {
  const categories = graphData.categories || []
  const centerItemId = Number(graphData.centerItemId)

  const nodes = (graphData.nodes || []).map(node => ({
    ...node,
    id: String(node.id),
    name: node.name,
    draggable: true,
    value: node.name,
    label: {
      show: true,
      color: '#1F2937',
      fontSize: node.id === centerItemId ? 14 : 11,
      fontWeight: node.id === centerItemId ? '700' : '500',
    },
    itemStyle: {
      shadowBlur: node.id === centerItemId ? 24 : 12,
      shadowColor: 'rgba(15, 23, 42, 0.12)',
      borderColor: '#FFFFFF',
      borderWidth: 2,
    },
  }))

  return {
    backgroundColor: 'transparent',
    animationDuration: 400,
    series: [
      {
        type: 'graph',
        layout: 'force',
        roam: true,
        focusNodeAdjacency: true,
        force: {
          repulsion: 260,
          edgeLength: [90, 150],
          gravity: 0.08,
        },
        categories,
        data: nodes,
        links: (graphData.edges || []).map(edge => ({
          source: String(edge.source),
          target: String(edge.target),
          value: edge.label,
          label: {
            show: true,
            formatter: edge.label,
            fontSize: 10,
            color: '#64748B',
          },
          lineStyle: {
            color: '#94A3B8',
            width: 1.5,
            curveness: 0.08,
          },
        })),
        label: {
          position: 'right',
        },
        symbolSize(value, params) {
          return params.data.id === String(centerItemId) ? 52 : Math.max(params.data.symbolSize || 26, 26)
        },
        lineStyle: {
          opacity: 0.9,
        },
        emphasis: {
          scale: true,
          lineStyle: {
            width: 2.5,
          },
        },
      },
    ],
  }
}

Component({
  properties: {
    graphData: {
      type: Object,
      value: null,
      observer: 'updateChart',
    },
  },

  lifetimes: {
    ready() {
      this.initChart()
    },

    detached() {
      if (this.chart) {
        this.chart.dispose()
        this.chart = null
      }
    },
  },

  methods: {
    initChart() {
      const query = wx.createSelectorQuery().in(this)
      query
        .select('#knowledge-graph')
        .fields({ node: true, size: true })
        .exec((res) => {
          if (!res || !res[0] || !res[0].node) {
            console.error('[echarts-graph] 未获取到 canvas 节点')
            return
          }

          const canvasNode = res[0].node
          const width = res[0].width
          const height = res[0].height
          const dpr = wx.getWindowInfo().pixelRatio

          canvasNode.width = width * dpr
          canvasNode.height = height * dpr

          patchCanvasForEcharts(canvasNode)

          const chart = echarts.init(canvasNode, null, {
            width: width,
            height: height,
            devicePixelRatio: dpr,
          })

          this.chart = chart
          this.canvasNode = canvasNode

          if (this.properties.graphData) {
            chart.setOption(buildOption(this.properties.graphData), true)
          }
        })
    },

    updateChart(graphData) {
      if (!this.chart || !graphData || !graphData.nodes) {
        return
      }
      this.chart.setOption(buildOption(graphData), true)
    },

    // 包装事件对象
    _wrapEvent(touch) {
      return {
        zrX: touch.x,
        zrY: touch.y,
        preventDefault: function () {},
        stopPropagation: function () {},
        stopImmediatePropagation: function () {},
      }
    },

    touchStart(e) {
      if (!this.chart || !e.touches.length) return
      const touch = e.touches[0]
      // 记录起始位置，用于判断是点击还是拖拽
      this._touchStartPos = { x: touch.x, y: touch.y }
      const handler = this.chart.getZr().handler
      handler.dispatch('mousedown', this._wrapEvent(touch))
    },

    touchMove(e) {
      if (!this.chart || !e.touches.length) return
      const handler = this.chart.getZr().handler
      handler.dispatch('mousemove', this._wrapEvent(e.touches[0]))
    },

    touchEnd(e) {
      if (!this.chart) return
      const touch = e.changedTouches ? e.changedTouches[0] : null
      if (!touch) return

      const handler = this.chart.getZr().handler
      handler.dispatch('mouseup', this._wrapEvent(touch))

      // 判断是否为点击（移动距离 < 10px）
      const start = this._touchStartPos
      if (!start) return
      const dx = Math.abs(touch.x - start.x)
      const dy = Math.abs(touch.y - start.y)
      if (dx > 10 || dy > 10) return

      // 是点击，手动查找被点击的节点
      this._findTappedNode(touch.x, touch.y)
    },

    // 手动检测点击了哪个节点
    _findTappedNode(x, y) {
      if (!this.chart || !this.properties.graphData) return

      const nodes = this.properties.graphData.nodes || []
      // 获取 echarts 当前所有节点的像素坐标
      const series = this.chart.getModel().getSeriesByIndex(0)
      if (!series) return

      const coordSys = series.coordinateSystem
      const data = series.getData()
      const hitRadius = 30

      for (let i = 0; i < data.count(); i++) {
        const layout = data.getItemLayout(i)
        if (!layout) continue

        const nodeX = layout[0]
        const nodeY = layout[1]
        const dist = Math.sqrt((x - nodeX) * (x - nodeX) + (y - nodeY) * (y - nodeY))

        if (dist < hitRadius) {
          const nodeData = nodes[i]
          if (nodeData && nodeData.id) {
            this.triggerEvent('nodetap', { itemId: nodeData.id })
          }
          return
        }
      }
    },
  },
})
