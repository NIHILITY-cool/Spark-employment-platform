<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { MapChart } from 'echarts/charts'
import { TooltipComponent, VisualMapComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { ArrowRight, BriefcaseBusiness, MapPin, MapPinned, RefreshCw } from '@lucide/vue'
import { apiRequest } from '../api/client'
import chinaGeoJson from '../assets/china.geo.json'

const props = defineProps({ apiBase: { type: String, required: true } })
const emit = defineEmits(['browse-city'])

echarts.use([MapChart, TooltipComponent, VisualMapComponent, CanvasRenderer])
echarts.registerMap('china-student-region', chinaGeoJson)

const loading = ref(true)
const detailLoading = ref(false)
const error = ref('')
const dashboard = ref(null)
const detail = ref(null)
const selectedProvince = ref('')
const metric = ref('jobs')
const mapElement = ref(null)
let mapChart = null
let detailRequest = 0

const provinceDemand = computed(() => dashboard.value?.provinceDemand || [])
const locatedJobCount = computed(() => provinceDemand.value.reduce((sum, item) => sum + Number(item.jobCount || 0), 0))
const selectedProvinceMetric = computed(() => provinceDemand.value.find((item) => item.key === selectedProvince.value))
const current = computed(() => detail.value || dashboard.value || emptyDashboard())
const entryRate = computed(() => {
  const total = Number(current.value.summary?.jobCount || 0)
  return total ? Math.round(Number(current.value.summary?.entryFriendlyCount || 0) / total * 100) : 0
})
const averageSalary = computed(() => {
  const item = selectedProvinceMetric.value
  if (item?.averageSalaryMin && item?.averageSalaryMax) return (Number(item.averageSalaryMin) + Number(item.averageSalaryMax)) / 2
  return Number(current.value.summary?.averageSalary || 0)
})
const maxCityJobs = computed(() => Math.max(1, ...(current.value.cities || []).map((item) => Number(item.jobCount || 0))))
const mapData = computed(() => {
  const byProvince = new Map(provinceDemand.value.map((item) => [item.key, item]))
  return chinaGeoJson.features.map((feature) => {
    const geoName = feature.properties?.name || ''
    const province = provinceDisplayName(geoName)
    const item = byProvince.get(province) || { key: province, jobCount: 0, averageSalaryMin: null, averageSalaryMax: null }
    return {
      name: geoName,
      value: metricValue(item),
      item,
    }
  })
})

async function loadOverview() {
  loading.value = true
  error.value = ''
  try {
    dashboard.value = await apiRequest(props.apiBase, '/university/market-dashboard')
    if (!dashboard.value?.summary || !dashboard.value?.provinceDemand) throw new Error('地区数据结构不完整')
    const preferred = dashboard.value.provinceDemand.find((item) => item.key === '广东') || dashboard.value.provinceDemand[0]
    selectedProvince.value = preferred?.key || ''
  } catch (cause) {
    error.value = cause.message || '地区岗位数据暂时不可用'
  } finally {
    loading.value = false
    nextTick(renderMap)
  }
}

async function loadProvince(province) {
  if (!province) return
  const requestId = ++detailRequest
  detailLoading.value = true
  try {
    const payload = await apiRequest(props.apiBase, `/university/market-dashboard?city=${encodeURIComponent(province)}`)
    if (requestId === detailRequest) detail.value = payload
  } catch (cause) {
    if (requestId === detailRequest) error.value = cause.message || `${province}岗位数据暂时不可用`
  } finally {
    if (requestId === detailRequest) detailLoading.value = false
  }
}

function selectProvince(province) {
  if (!province || !provinceDemand.value.some((item) => item.key === province)) return
  selectedProvince.value = province
}

function renderMap() {
  if (!mapElement.value) return
  if (!mapChart) {
    mapChart = echarts.init(mapElement.value)
    mapChart.on('click', (params) => selectProvince(provinceDisplayName(params.name)))
  }
  const max = Math.max(1, ...mapData.value.map((item) => Number(item.value || 0)))
  mapChart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      borderWidth: 0,
      padding: 0,
      formatter: ({ name, data }) => mapTooltip(provinceDisplayName(name), data?.item),
      extraCssText: 'box-shadow: 0 12px 30px rgba(14,47,62,.18);',
    },
    visualMap: { min: 0, max, show: false, inRange: { color: ['#edf5f2', '#b9d6ca', '#6aa78f', '#24644f'] } },
    series: [{
      type: 'map',
      map: 'china-student-region',
      roam: false,
      selectedMode: false,
      data: mapData.value,
      nameProperty: 'name',
      layoutCenter: ['49%', '53%'],
      layoutSize: '108%',
      label: { show: false },
      itemStyle: { borderColor: '#fff', borderWidth: 1, areaColor: '#edf4f1' },
      emphasis: { label: { show: true, color: '#173e50', fontSize: 11, fontWeight: 700 }, itemStyle: { areaColor: '#c7ec74', borderColor: '#173e50' } },
    }],
  }, true)
}

function mapTooltip(province, item = {}) {
  const salary = salaryRange(item)
  return `<div class="student-region-tooltip"><strong>${province}</strong><span>${formatNumber(item.jobCount)} 个岗位</span><p>平均薪资区间：${salary}</p></div>`
}

function metricValue(item) {
  if (metric.value === 'salary') {
    if (!item?.averageSalaryMin || !item?.averageSalaryMax) return 0
    return (Number(item.averageSalaryMin) + Number(item.averageSalaryMax)) / 2
  }
  return Number(item?.jobCount || 0)
}

function salaryRange(item) {
  if (!item?.averageSalaryMin || !item?.averageSalaryMax) return '暂无'
  return `${Math.round(Number(item.averageSalaryMin) / 1000)}K-${Math.round(Number(item.averageSalaryMax) / 1000)}K`
}

function provinceDisplayName(value) {
  return String(value || '')
    .replace(/特别行政区$/, '')
    .replace(/维吾尔自治区$/, '')
    .replace(/壮族自治区$/, '')
    .replace(/回族自治区$/, '')
    .replace(/自治区$/, '')
    .replace(/省$/, '')
    .replace(/市$/, '')
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString()
}

function compactSalary(value) {
  return value ? `${Math.round(Number(value) / 1000)}K` : '暂无'
}

function barWidth(value) {
  return `${Math.min(100, Math.max(4, Math.round(Number(value || 0) / maxCityJobs.value * 100)))}%`
}

function emptyDashboard() {
  return { summary: {}, cities: [], industries: [], jobCategories: [] }
}

function resizeMap() {
  mapChart?.resize()
}

watch(selectedProvince, (province) => loadProvince(province))
watch([mapData, metric], () => nextTick(renderMap), { deep: true })

onMounted(() => {
  loadOverview()
  window.addEventListener('resize', resizeMap)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeMap)
  mapChart?.dispose()
  mapChart = null
})
</script>

<template>
  <section class="student-region-page">
    <header class="student-region-banner">
      <div>
        <p class="eyebrow">岗位地区分布 · 近期公开岗位</p>
        <h1>先看机会在哪，<br />再决定去哪里。</h1>
        <p>按省份比较岗位规模与薪资，点开地区后查看真正可投递的热门城市和岗位方向。</p>
      </div>
      <div class="student-region-summary" aria-label="地区岗位摘要">
        <div><span>覆盖省份</span><strong>{{ provinceDemand.filter((item) => item.jobCount > 0).length }}</strong></div>
        <div><span>可定位岗位</span><strong>{{ formatNumber(locatedJobCount) }}</strong></div>
        <div><span>数据批次</span><strong>{{ dashboard?.statDate || '-' }}</strong></div>
      </div>
    </header>

    <p v-if="error" class="student-region-error">{{ error }} <button type="button" @click="loadOverview"><RefreshCw :size="14" />重新加载</button></p>

    <div class="student-region-layout">
      <section class="student-map-panel">
        <div class="student-region-head">
          <div><p class="eyebrow">全国机会地图</p><h2>省份岗位热度</h2></div>
          <div class="student-map-toggle" role="group" aria-label="地图指标">
            <button type="button" :class="{ active: metric === 'jobs' }" @click="metric = 'jobs'">岗位量</button>
            <button type="button" :class="{ active: metric === 'salary' }" @click="metric = 'salary'">平均薪资</button>
          </div>
        </div>
        <div v-if="loading" class="student-region-loading">正在读取地区岗位数据…</div>
        <div ref="mapElement" class="student-region-map" aria-label="全国岗位地区分布地图"></div>
        <p class="student-map-note"><MapPinned :size="15" />省份数据包含已确认归属的城市岗位。</p>
      </section>

      <aside class="student-region-decision">
        <div class="decision-heading">
          <span>当前地区</span>
          <h2>{{ selectedProvince || '请选择省份' }}</h2>
          <i v-if="detailLoading">正在汇总该地区…</i>
        </div>
        <div class="decision-metrics">
          <div><span>岗位机会</span><strong>{{ formatNumber(current.summary?.jobCount || selectedProvinceMetric?.jobCount) }}</strong></div>
          <div><span>平均月薪</span><strong>{{ compactSalary(averageSalary) }}</strong></div>
          <div><span>低经验门槛</span><strong>{{ entryRate }}%</strong></div>
        </div>
        <section class="decision-section">
          <div class="decision-title"><span>优先查看城市</span><small>点击进入岗位市场</small></div>
          <div class="decision-city-list">
            <button v-for="city in current.cities.slice(0, 6)" :key="city.key" type="button" @click="emit('browse-city', city.key)">
              <span><MapPin :size="13" />{{ city.key }}</span><i><b :style="{ width: barWidth(city.jobCount) }"></b></i><strong>{{ formatNumber(city.jobCount) }}</strong><ArrowRight :size="15" />
            </button>
            <p v-if="!current.cities.length">暂无可确认的城市岗位。</p>
          </div>
        </section>
      </aside>
    </div>

    <section class="student-region-signals">
      <div class="student-signal-column">
        <div class="student-region-head"><div><p class="eyebrow">岗位方向</p><h2>{{ selectedProvince }}更需要什么人</h2></div><BriefcaseBusiness :size="20" /></div>
        <ol>
          <li v-for="(item, index) in current.jobCategories.slice(0, 8)" :key="item.key"><b>{{ String(index + 1).padStart(2, '0') }}</b><span>{{ item.key }}</span><i><em :style="{ width: barWidth(item.jobCount) }"></em></i><strong>{{ formatNumber(item.jobCount) }}</strong></li>
        </ol>
      </div>
      <div class="student-signal-column">
        <div class="student-region-head"><div><p class="eyebrow">行业去向</p><h2>机会集中在哪些行业</h2></div><MapPinned :size="20" /></div>
        <ol>
          <li v-for="(item, index) in current.industries.slice(0, 8)" :key="item.key"><b>{{ String(index + 1).padStart(2, '0') }}</b><span>{{ item.key }}</span><i><em :style="{ width: barWidth(item.jobCount) }"></em></i><strong>{{ formatNumber(item.jobCount) }}</strong></li>
        </ol>
      </div>
    </section>
  </section>
</template>
