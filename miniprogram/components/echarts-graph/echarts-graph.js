const { echarts, patchCanvasForEcharts } = require('../../utils/echarts-wx')

function buildOption(graphData) {
  const categories = graphData.categories || []
  const centerItemId = Number(graphData.centerItemId)
  const nodes = (graphData.nodes || []).map(node => ({
    ...node,
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
    tooltip: {
      trigger: 'item',
      confine: true,
      formatter(params) {
        if (params.dataType === 'edge') {
          return `${params.data.source} → ${params.data.target}<br/>关系：${params.data.label || params.data.value || 'related_to'}`
        }
        const category = categories[params.data.category]
        return `${params.data.name}<br/>分类：${category ? category.name : '未知'}`
      },
    },
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
          source: edge.source,
          target: edge.target,
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
          return params.data.id === centerItemId ? 52 : Math.max(params.data.symbolSize || 26, 26)
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

  data: {
    echarts,
    ec: {
      lazyLoad: true,
    },
  },

  lifetimes: {
    ready() {
      this.ecComponent = this.selectComponent('#knowledge-graph')
      if (this.ecComponent) {
        this.ecComponent.init((canvas, width, height, dpr) => {
          patchCanvasForEcharts(canvas)
          const chart = echarts.init(canvas, null, {
            width,
            height,
            devicePixelRatio: dpr,
          })
          canvas.setChart(chart)
          this.chart = chart
          this.bindChartEvents()
          if (this.properties.graphData) {
            chart.setOption(buildOption(this.properties.graphData), true)
          }
          return chart
        })
      }
    },

    detached() {
      if (this.chart) {
        this.chart.dispose()
        this.chart = null
      }
    },
  },

  methods: {
    bindChartEvents() {
      if (!this.chart) {
        return
      }
      this.chart.off('click')
      this.chart.on('click', params => {
        if (params.dataType !== 'node' || !params.data || !params.data.id) {
          return
        }
        this.triggerEvent('nodetap', { itemId: params.data.id })
      })
    },

    updateChart(graphData) {
      if (!this.chart || !graphData || !graphData.nodes) {
        return
      }
      this.chart.setOption(buildOption(graphData), true)
    },
  },
})
