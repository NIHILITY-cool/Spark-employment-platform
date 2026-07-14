<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { BarChart, LineChart } from 'echarts/charts'
import { AriaComponent, DataZoomComponent, GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import * as echarts from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { CircleAlert, LoaderCircle, RefreshCw } from '@lucide/vue'
import { apiRequest } from '../api/client'

echarts.use([
  BarChart,
  LineChart,
  AriaComponent,
  DataZoomComponent,
  GridComponent,
  LegendComponent,
  TooltipComponent,
  CanvasRenderer,
])

const props = defineProps({
  apiBase: { type: String, required: true },
  city: { type: String, default: '' },
})

const loading = ref(true)
const error = ref('')
const report = ref(null)
const chartElement = ref(null)
let chart = null
let resizeObserver = null

const salarySampleTotal = computed(() => (report.value?.industries || [])
  .reduce((sum, item) => sum + Number(item.salarySampleCount || 0), 0))
const classifiedJobTotal = computed(() => (report.value?.industries || [])
  .reduce((sum, item) => sum + Number(item.jobCount || 0), 0))
const salaryCoverage = computed(() => classifiedJobTotal.value
  ? Math.round(salarySampleTotal.value / classifiedJobTotal.value * 100) : 0)
const highestPaidIndustry = computed(() => [...(report.value?.industries || [])]
  .filter((item) => item.averageSalary)
  .sort((a, b) => b.averageSalary - a.averageSalary)[0])

async function loadReport() {
  loading.value = true
  error.value = ''
  try {
    const params = new URLSearchParams()
    if (props.city) params.set('city', props.city)
    report.value = await apiRequest(props.apiBase, `/university/industry-salary-distribution?${params}`)
    await nextTick()
    renderChart()
  } catch (cause) {
    error.value = cause.message || '行业薪资数据加载失败'
    report.value = null
    chart?.clear()
  } finally {
    loading.value = false
  }
}

function renderChart() {
  const rows = report.value?.industries || []
  if (!chartElement.value || !rows.length) return
  if (!chart) chart = echarts.init(chartElement.value)
  const compact = chartElement.value.clientWidth < 680
  const salaryBands = [
    ['5K 以下', 'below5k', '#9dc7ba'],
    ['5K-8K', 'from5kTo8k', '#5f9d8c'],
    ['8K-12K', 'from8kTo12k', '#317568'],
    ['12K-20K', 'from12kTo20k', '#69648e'],
    ['20K 以上', 'above20k', '#bbb45f'],
  ]
  chart.setOption({
    animationDuration: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 500,
    color: salaryBands.map((item) => item[2]),
    aria: { enabled: true, description: '行业岗位薪资档位分布与平均月薪图' },
    legend: { top: 0, left: 0, itemWidth: 12, itemHeight: 8, textStyle: { color: '#5d746f', fontSize: 10 } },
    grid: { left: compact ? 42 : 52, right: compact ? 42 : 58, top: compact ? 92 : 70, bottom: 64 },
    tooltip: {
      trigger: 'axis', backgroundColor: '#0b2f50', borderWidth: 0, padding: 12,
      textStyle: { color: '#fff', fontSize: 11 },
      formatter(params) {
        const row = rows[params[0].dataIndex]
        const bands = params.filter((item) => item.seriesType === 'bar')
          .map((item) => `${item.marker}${item.seriesName}：${Number(item.value).toLocaleString()} 个`).join('<br>')
        const average = row.averageSalary ? `${(row.averageSalary / 1000).toFixed(1)}K/月` : '暂无'
        return `<strong>${row.industry}</strong><br>岗位样本：${row.jobCount.toLocaleString()} 个<br>平均月薪：${average}<br>${bands}`
      },
    },
    xAxis: {
      type: 'category', data: rows.map((item) => item.industry),
      axisLine: { lineStyle: { color: '#ccd9d5' } }, axisTick: { show: false },
      axisLabel: { color: '#4f6965', fontSize: 10, interval: 0, rotate: compact ? 34 : 0 },
    },
    yAxis: [
      { type: 'value', name: '岗位数', nameTextStyle: { color: '#758985', fontSize: 9 }, splitLine: { lineStyle: { color: '#edf2f0' } }, axisLabel: { color: '#758985', fontSize: 9 } },
      { type: 'value', name: '平均月薪', nameTextStyle: { color: '#b9684e', fontSize: 9 }, splitLine: { show: false }, axisLabel: { color: '#b9684e', fontSize: 9, formatter: (value) => `${Math.round(value / 1000)}K` } },
    ],
    dataZoom: [
      { type: 'inside', start: 0, end: compact ? 55 : 100 },
      { type: 'slider', start: 0, end: compact ? 55 : 100, height: 14, bottom: 8, borderColor: '#d8e3df', fillerColor: 'rgba(67,130,111,.18)', handleStyle: { color: '#43826f' }, textStyle: { color: '#71847f', fontSize: 9 } },
    ],
    series: [
      ...salaryBands.map(([name, key]) => ({ name, type: 'bar', stack: 'salary', barMaxWidth: 34, data: rows.map((item) => item[key]), emphasis: { focus: 'series' } })),
      { name: '平均月薪', type: 'line', yAxisIndex: 1, data: rows.map((item) => item.averageSalary), symbolSize: 7, lineStyle: { width: 2, color: '#d46f50' }, itemStyle: { color: '#d46f50', borderColor: '#fff', borderWidth: 2 }, connectNulls: false },
    ],
  }, true)
  if (!resizeObserver) {
    resizeObserver = new ResizeObserver(() => chart?.resize())
    resizeObserver.observe(chartElement.value)
  }
}

watch(() => props.city, loadReport)
onMounted(loadReport)
onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  chart?.dispose()
})
</script>

<template>
  <section class="industry-salary-section dashboard-panel">
    <div class="university-section-head">
      <div><p class="eyebrow">岗位文本关键词分类</p><h2>十大行业薪资分布</h2></div>
      <span>{{ city || '全国' }}，月薪口径</span>
    </div>

    <div v-if="error" class="university-error salary-panel-status">
      <CircleAlert :size="18" />
      <span>{{ error }}</span>
      <button class="command secondary" type="button" @click="loadReport"><RefreshCw :size="15" />重新加载</button>
    </div>
    <div v-else-if="loading && !report" class="workspace-loading salary-panel-status">
      <LoaderCircle class="spin" :size="24" /><span>正在计算行业薪资分布</span>
    </div>
    <template v-else-if="report?.industries?.length">
      <div class="industry-salary-meta">
        <div><span>有效薪资样本</span><strong>{{ salarySampleTotal.toLocaleString() }}</strong><small>覆盖 {{ salaryCoverage }}% 分类岗位</small></div>
        <div><span>平均薪资最高</span><strong>{{ highestPaidIndustry?.industry || '暂无' }}</strong><small>{{ highestPaidIndustry?.averageSalary ? `${(highestPaidIndustry.averageSalary / 1000).toFixed(1)}K/月` : '暂无有效薪资' }}</small></div>
        <p>{{ report.classificationBasis }}</p>
      </div>
      <div ref="chartElement" class="industry-salary-chart" role="img" aria-label="十大行业的薪资档位岗位数与平均月薪图表"></div>
    </template>
    <p v-else class="empty-dashboard-state">当前地区没有可用的行业薪资样本。</p>
  </section>
</template>
