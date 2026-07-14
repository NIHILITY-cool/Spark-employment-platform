<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { BarChart, LineChart } from 'echarts/charts'
import { AriaComponent, DataZoomComponent, GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import * as echarts from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import {
  BriefcaseBusiness,
  Building2,
  ChartNoAxesCombined,
  Check,
  CircleAlert,
  Database,
  GraduationCap,
  Lightbulb,
  LoaderCircle,
  MapPinned,
  Home,
  RefreshCw,
  SlidersHorizontal,
  Sparkles,
} from '@lucide/vue'
import { apiRequest } from '../api/client'
import SearchSelect from './SearchSelect.vue'

echarts.use([BarChart, LineChart, AriaComponent, DataZoomComponent, GridComponent, LegendComponent, TooltipComponent, CanvasRenderer])

const props = defineProps({
  apiBase: { type: String, required: true },
  cityOptions: { type: Array, default: () => [] },
})
const emit = defineEmits(['back-to-portal'])

const loading = ref(true)
const error = ref('')
const analysis = ref(null)
const major = ref('数据科学与大数据技术')
const city = ref('')
const selectedSkills = ref(new Set())
const industrySalary = ref(null)
const salaryChartElement = ref(null)
let salaryChart = null
let chartResizeObserver = null

const presetSkills = {
  数据科学与大数据技术: ['Python', 'SQL', 'Spark'],
  计算机科学与技术: ['Java', 'MySQL', 'Git'],
  软件工程: ['JavaScript', 'Vue', 'TypeScript'],
  统计学: ['SQL', 'Python', 'Excel'],
  人工智能: ['Python', 'PyTorch', '机器学习'],
}

const majors = computed(() => Object.keys(analysis.value?.availableMajors || presetSkills))
const friendlyRate = computed(() => {
  const summary = analysis.value?.summary
  return summary?.jobCount ? Math.round(summary.entryFriendlyCount / summary.jobCount * 100) : 0
})
const averageSalary = computed(() => {
  const summary = analysis.value?.summary
  if (!summary?.averageSalaryMin || !summary?.averageSalaryMax) return '暂无'
  return `${Math.round(summary.averageSalaryMin / 1000)}K-${Math.round(summary.averageSalaryMax / 1000)}K`
})
const skillCoverage = computed(() => {
  const skills = analysis.value?.skills || []
  const total = skills.reduce((sum, item) => sum + item.jobCount, 0)
  const covered = skills.reduce((sum, item) => sum + (selectedSkills.value.has(item.key) ? item.jobCount : 0), 0)
  return total ? Math.round(covered / total * 100) : 0
})
const missingPriority = computed(() => (analysis.value?.skills || [])
  .filter((item) => !selectedSkills.value.has(item.key)).slice(0, 3).map((item) => item.key))
const matrixCities = computed(() => [...new Set((analysis.value?.regionalMatrix || []).map((item) => item.city))])
const matrixCategories = computed(() => [...new Set((analysis.value?.regionalMatrix || []).map((item) => item.category))])
const maxMatrixValue = computed(() => Math.max(1, ...(analysis.value?.regionalMatrix || []).map((item) => item.jobCount)))
const salarySampleTotal = computed(() => (industrySalary.value?.industries || [])
  .reduce((sum, item) => sum + Number(item.salarySampleCount || 0), 0))
const classifiedJobTotal = computed(() => (industrySalary.value?.industries || [])
  .reduce((sum, item) => sum + Number(item.jobCount || 0), 0))
const salaryCoverage = computed(() => classifiedJobTotal.value
  ? Math.round(salarySampleTotal.value / classifiedJobTotal.value * 100) : 0)
const highestPaidIndustry = computed(() => [...(industrySalary.value?.industries || [])]
  .filter((item) => item.averageSalary)
  .sort((a, b) => b.averageSalary - a.averageSalary)[0])

async function loadAnalysis(resetSkills = false) {
  loading.value = true
  error.value = ''
  try {
    const params = new URLSearchParams({ major: major.value })
    if (city.value) params.set('city', city.value)
    const salaryParams = new URLSearchParams()
    if (city.value) salaryParams.set('city', city.value)
    const [analysisPayload, salaryPayload] = await Promise.all([
      apiRequest(props.apiBase, `/university/training-alignment?${params}`),
      apiRequest(props.apiBase, `/university/industry-salary-distribution?${salaryParams}`),
    ])
    analysis.value = analysisPayload
    industrySalary.value = salaryPayload
    if (resetSkills || !selectedSkills.value.size) {
      const available = new Set(analysis.value.skills.map((item) => item.key))
      selectedSkills.value = new Set((presetSkills[major.value] || []).filter((item) => available.has(item)))
    }
    await nextTick()
    renderSalaryChart()
  } catch (cause) {
    error.value = cause.message
  } finally {
    loading.value = false
  }
}

function renderSalaryChart() {
  if (!salaryChartElement.value || !industrySalary.value?.industries?.length) return
  if (!salaryChart) salaryChart = echarts.init(salaryChartElement.value)
  const rows = industrySalary.value.industries
  const compact = salaryChartElement.value.clientWidth < 680
  const salaryBands = [
    ['5K 以下', 'below5k', '#9dc7ba'],
    ['5K-8K', 'from5kTo8k', '#5f9d8c'],
    ['8K-12K', 'from8kTo12k', '#317568'],
    ['12K-20K', 'from12kTo20k', '#69648e'],
    ['20K 以上', 'above20k', '#bbb45f'],
  ]
  salaryChart.setOption({
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
  if (!chartResizeObserver) {
    chartResizeObserver = new ResizeObserver(() => salaryChart?.resize())
    chartResizeObserver.observe(salaryChartElement.value)
  }
}

function changeMajor() {
  selectedSkills.value = new Set()
  loadAnalysis(true)
}

function toggleSkill(skill) {
  const next = new Set(selectedSkills.value)
  if (next.has(skill)) next.delete(skill)
  else next.add(skill)
  selectedSkills.value = next
}

function matrixCell(cityName, category) {
  return analysis.value?.regionalMatrix.find((item) => item.city === cityName && item.category === category)?.jobCount || 0
}

function matrixStyle(value) {
  const strength = value / maxMatrixValue.value
  return { background: `rgba(67, 130, 111, ${0.08 + strength * 0.82})`, color: strength > 0.52 ? '#fff' : '#174052' }
}

function barWidth(value, items) {
  const max = Math.max(1, ...items.map((item) => item.jobCount))
  return `${Math.max(3, Math.round(value / max * 100))}%`
}

onMounted(() => loadAnalysis(true))
onBeforeUnmount(() => {
  chartResizeObserver?.disconnect()
  salaryChart?.dispose()
})
</script>

<template>
  <section class="university-workspace">
    <header class="university-banner">
      <div class="university-banner-copy">
        <p class="eyebrow">高校培养参考 · 公开岗位证据</p>
        <h1>从市场需求反推训练重点。</h1>
        <p>不使用毕业去向数据，不评价培养质量；只回答岗位在哪里、需要什么、训练组合能覆盖多少需求。</p>
      </div>
      <div class="university-banner-actions">
        <button class="university-button" type="button" title="返回初始页" @click="emit('back-to-portal')"><Home :size="15" /><span>返回初始页</span></button>
        <div class="data-stamp"><Database :size="18" /><span>数据批次</span><strong>2026-07-11</strong></div>
      </div>
    </header>

    <form class="analysis-controls" @submit.prevent="loadAnalysis(false)">
      <div class="analysis-control"><GraduationCap :size="16" /><span>专业方向</span><SearchSelect v-model="major" class="analysis-picker" label="专业方向" placeholder="搜索专业方向" :allow-empty="false" :options="majors" @select="changeMajor" /></div>
      <div class="analysis-control"><MapPinned :size="16" /><span>地区范围</span><SearchSelect v-model="city" class="analysis-picker" label="地区范围" placeholder="搜索地区" empty-label="全国岗位" :options="cityOptions" /></div>
      <button class="command primary" type="submit" :disabled="loading"><LoaderCircle v-if="loading" class="spin" :size="16" /><RefreshCw v-else :size="16" />更新分析</button>
    </form>

    <div v-if="error" class="university-error"><CircleAlert :size="18" /><span>{{ error }}</span><button class="command secondary" type="button" @click="loadAnalysis(false)">重新连接</button></div>
    <div v-if="loading && !analysis" class="workspace-loading"><LoaderCircle :size="28" /><span>正在聚合岗位、地区和技能需求</span></div>

    <template v-else-if="analysis">
      <section class="evidence-strip" aria-label="分析证据摘要">
        <div><BriefcaseBusiness :size="18" /><span>岗位样本</span><strong>{{ analysis.summary.jobCount.toLocaleString() }}</strong></div>
        <div><GraduationCap :size="18" /><span>低经验门槛</span><strong>{{ friendlyRate }}%</strong></div>
        <div><ChartNoAxesCombined :size="18" /><span>平均月薪</span><strong>{{ averageSalary }}</strong></div>
        <div><Sparkles :size="18" /><span>技能信号</span><strong>{{ analysis.summary.extractedSkillCount }}</strong></div>
      </section>

      <div class="alignment-layout">
        <section class="scenario-section">
          <div class="university-section-head"><div><p class="eyebrow">培养场景 · 可编辑</p><h2>计划强化技能组合</h2></div><SlidersHorizontal :size="21" /></div>
          <div class="coverage-display"><strong>{{ skillCoverage }}%</strong><span>Top 技能需求场景覆盖率</span><i><b :style="{ width: `${skillCoverage}%` }"></b></i></div>
          <div class="demand-skill-list">
            <button v-for="skill in analysis.skills" :key="skill.key" type="button" :class="{ selected: selectedSkills.has(skill.key) }" :aria-pressed="selectedSkills.has(skill.key)" @click="toggleSkill(skill.key)">
              <span class="skill-check"><Check v-if="selectedSkills.has(skill.key)" :size="13" /></span>
              <span><strong>{{ skill.key }}</strong><small>{{ skill.jobCount }} 个岗位提及</small></span>
              <i><b :style="{ width: barWidth(skill.jobCount, analysis.skills) }"></b></i>
            </button>
          </div>
          <p class="scenario-note"><Lightbulb :size="16" />当前组合仍优先缺少：{{ missingPriority.join('、') || '无' }}。该比例是岗位技能覆盖场景，不是课程质量评分。</p>
        </section>

        <section class="demand-section">
          <div class="university-section-head"><div><p class="eyebrow">岗位结构</p><h2>行业与学历需求</h2></div><Building2 :size="21" /></div>
          <div class="demand-columns">
            <div><span>主要行业</span><ol><li v-for="item in analysis.industries.slice(0, 6)" :key="item.key"><b>{{ item.key }}</b><i><em :style="{ width: barWidth(item.jobCount, analysis.industries) }"></em></i><strong>{{ item.jobCount }}</strong></li></ol></div>
            <div><span>学历要求</span><ol><li v-for="item in analysis.education.slice(0, 6)" :key="item.key"><b>{{ item.key }}</b><i><em :style="{ width: barWidth(item.jobCount, analysis.education) }"></em></i><strong>{{ item.jobCount }}</strong></li></ol></div>
          </div>
        </section>
      </div>

      <section class="industry-salary-section">
        <div class="university-section-head">
          <div><p class="eyebrow">岗位文本关键词分类</p><h2>行业薪资分布</h2></div>
          <span>{{ city || '全国' }} · 月薪口径</span>
        </div>
        <div class="industry-salary-meta">
          <div><span>有效薪资样本</span><strong>{{ salarySampleTotal.toLocaleString() }}</strong><small>覆盖 {{ salaryCoverage }}% 分类岗位</small></div>
          <div><span>平均薪资最高</span><strong>{{ highestPaidIndustry?.industry || '暂无' }}</strong><small>{{ highestPaidIndustry?.averageSalary ? `${(highestPaidIndustry.averageSalary / 1000).toFixed(1)}K/月` : '暂无有效薪资' }}</small></div>
          <p>{{ industrySalary?.classificationBasis }}</p>
        </div>
        <div ref="salaryChartElement" class="industry-salary-chart" role="img" aria-label="十个行业的薪资档位岗位数与平均月薪 ECharts 图表"></div>
      </section>

      <section class="matrix-section">
        <div class="university-section-head"><div><p class="eyebrow">Spark 清洗岗位 · 即席聚合</p><h2>地区 × 岗位方向需求矩阵</h2></div><span>颜色越深，岗位样本越多</span></div>
        <div class="matrix-scroll">
          <div class="demand-matrix" :style="{ '--columns': matrixCategories.length }">
            <div class="matrix-corner">地区 / 方向</div><div v-for="category in matrixCategories" :key="category" class="matrix-column">{{ category }}</div>
            <template v-for="cityName in matrixCities" :key="cityName">
              <div class="matrix-row-label">{{ cityName }}</div>
              <div v-for="category in matrixCategories" :key="`${cityName}-${category}`" class="matrix-cell" :style="matrixStyle(matrixCell(cityName, category))" :title="`${cityName} · ${category}: ${matrixCell(cityName, category)} 个岗位`">{{ matrixCell(cityName, category) }}</div>
            </template>
          </div>
        </div>
      </section>

      <section class="guidance-section">
        <div class="university-section-head"><div><p class="eyebrow">规则建议</p><h2>可进入下一轮论证的方向</h2></div><Lightbulb :size="21" /></div>
        <ol><li v-for="(item, index) in analysis.suggestions" :key="item"><span>{{ String(index + 1).padStart(2, '0') }}</span><p>{{ item }}</p></li></ol>
        <p class="data-basis">{{ analysis.dataBasis }}</p>
      </section>
    </template>
  </section>
</template>
