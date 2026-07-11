<script setup>
import { computed, onMounted, ref } from 'vue'

const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://192.168.64.2:8082/api'
const loading = ref(false)
const usingDemo = ref(false)
const message = ref('')
const keyword = ref('')
const city = ref('')
const category = ref('')
const jobs = ref([])
const total = ref(0)
const cityStats = ref([])
const hotSkills = ref([])
const cityOptions = ref([])
const categoryOptions = ref([])
const activePicker = ref('')
const citySearch = ref('')
const categorySearch = ref('')
const activeOptionIndex = ref(-1)

const demoJobs = [
  { jobKey: 'ncss-demo-1', jobName: '大数据开发工程师', companyName: '华川数智科技', city: '成都', jobCategory: '大数据开发', salaryMin: 9000, salaryMax: 14000, educationRequirement: '本科及以上', experienceRequirement: '经验不限', industry: '计算机软件' },
  { jobKey: 'liepin-demo-2', jobName: '数据分析师', companyName: '西南云图信息', city: '重庆', jobCategory: '数据分析', salaryMin: 8000, salaryMax: 13000, educationRequirement: '本科', experienceRequirement: '1-3年', industry: '互联网/电子商务' },
  { jobKey: 'guopin-demo-3', jobName: 'Java 后端开发工程师', companyName: '国创智联', city: '北京', jobCategory: '后端开发', salaryMin: 11000, salaryMax: 18000, educationRequirement: '本科及以上', experienceRequirement: '经验不限', industry: '软件和信息技术服务业' },
]

const demoCities = [...new Set(demoJobs.map((job) => job.city))]
const demoCategories = [...new Set(demoJobs.map((job) => job.jobCategory))]
const headlineTotal = computed(() => (total.value || 11559).toLocaleString())
const matchingCities = computed(() => filterOptions(cityOptions.value, citySearch.value))
const matchingCategories = computed(() => filterOptions(categoryOptions.value, categorySearch.value))

function salary(job) {
  if (!job.salaryMin || !job.salaryMax) return '薪资面议'
  return `${Math.round(job.salaryMin / 1000)}K–${Math.round(job.salaryMax / 1000)}K`
}

function normalizeCity(value) {
  const normalized = String(value || '').trim().replace(/市+$/, '')
  return normalized === '中国' ? '全国' : normalized
}

function mergeCityStats(items) {
  const totals = new Map()
  for (const item of items) {
    const name = normalizeCity(item.dimensionKey)
    if (name) totals.set(name, (totals.get(name) || 0) + Number(item.metricValue || 0))
  }
  return [...totals.entries()]
    .map(([dimensionKey, metricValue]) => ({ dimensionKey, metricValue }))
    .sort((a, b) => b.metricValue - a.metricValue || a.dimensionKey.localeCompare(b.dimensionKey, 'zh-CN'))
}

function filterOptions(options, term) {
  const normalized = term.trim().toLocaleLowerCase()
  return normalized ? options.filter((item) => item.toLocaleLowerCase().includes(normalized)) : options
}

function pickerOptions(kind) {
  return kind === 'city' ? matchingCities.value : matchingCategories.value
}

function openPicker(kind) {
  activePicker.value = kind
  activeOptionIndex.value = pickerOptions(kind).length ? 0 : -1
}

function togglePicker(kind) {
  if (activePicker.value === kind) {
    activePicker.value = ''
    return
  }
  openPicker(kind)
}

function updatePickerSearch(kind) {
  const query = kind === 'city' ? citySearch.value : categorySearch.value
  const selected = kind === 'city' ? city : category
  if (query !== selected.value) selected.value = ''
  openPicker(kind)
}

function choosePickerOption(kind, option) {
  if (kind === 'city') {
    city.value = option
    citySearch.value = option
  } else {
    category.value = option
    categorySearch.value = option
  }
  activePicker.value = ''
  activeOptionIndex.value = -1
}

function clearPicker(kind) {
  if (kind === 'city') {
    city.value = ''
    citySearch.value = ''
  } else {
    category.value = ''
    categorySearch.value = ''
  }
  activePicker.value = ''
}

function handlePickerKeydown(kind, event) {
  const options = pickerOptions(kind)
  if (event.key === 'ArrowDown') {
    event.preventDefault()
    if (activePicker.value !== kind) openPicker(kind)
    else activeOptionIndex.value = Math.min(activeOptionIndex.value + 1, options.length - 1)
  } else if (event.key === 'ArrowUp') {
    event.preventDefault()
    activeOptionIndex.value = Math.max(activeOptionIndex.value - 1, 0)
  } else if (event.key === 'Enter' && activePicker.value === kind && activeOptionIndex.value >= 0) {
    event.preventDefault()
    choosePickerOption(kind, options[activeOptionIndex.value])
  } else if (event.key === 'Escape') {
    activePicker.value = ''
  }
}

async function loadMarket() {
  try {
    const [cityResponse, skillResponse] = await Promise.all([
      fetch(`${apiBase}/market/statistics/city_distribution`),
      fetch(`${apiBase}/market/statistics/hot_skills`),
    ])
    if (!cityResponse.ok || !skillResponse.ok) throw new Error('market unavailable')
    cityStats.value = mergeCityStats(await cityResponse.json())
    hotSkills.value = await skillResponse.json()
  } catch {
    cityStats.value = [
      { dimensionKey: '成都', metricValue: 1255 }, { dimensionKey: '北京', metricValue: 722 },
      { dimensionKey: '上海', metricValue: 745 }, { dimensionKey: '重庆', metricValue: 177 },
    ]
    hotSkills.value = [
      { dimensionKey: 'Python', metricValue: 841 }, { dimensionKey: 'Java', metricValue: 782 },
      { dimensionKey: 'SQL', metricValue: 669 }, { dimensionKey: 'Spark', metricValue: 315 },
    ]
  }
}

async function loadFilters() {
  try {
    const response = await fetch(`${apiBase}/jobs/filters`)
    if (!response.ok) throw new Error('filters unavailable')
    const payload = await response.json()
    cityOptions.value = Array.isArray(payload.cities)
      ? [...new Set(payload.cities.map(normalizeCity).filter(Boolean))].sort((a, b) => a.localeCompare(b, 'zh-CN'))
      : []
    categoryOptions.value = Array.isArray(payload.categories) ? payload.categories : []
  } catch {
    cityOptions.value = demoCities
    categoryOptions.value = demoCategories
  }
}

async function search() {
  loading.value = true
  message.value = ''
  const params = new URLSearchParams({ page: '1', size: '12' })
  if (keyword.value.trim()) params.set('keyword', keyword.value.trim())
  if (city.value) params.set('city', city.value)
  if (category.value) params.set('category', category.value)
  try {
    const response = await fetch(`${apiBase}/jobs?${params}`)
    if (!response.ok) throw new Error('jobs unavailable')
    const payload = await response.json()
    jobs.value = payload.records
    total.value = payload.total
    usingDemo.value = false
  } catch {
    jobs.value = demoJobs.filter((job) => (!city.value || job.city === city.value) && (!category.value || job.jobCategory === category.value) && (!keyword.value || `${job.jobName}${job.companyName}`.includes(keyword.value)))
    total.value = jobs.value.length
    usingDemo.value = true
    message.value = '当前显示演示数据：本机前端已启动，等待虚拟机后端服务开放后将自动读取真实岗位。'
  } finally {
    loading.value = false
  }
}

function reset() {
  keyword.value = ''
  clearPicker('city')
  clearPicker('category')
  search()
}

onMounted(async () => {
  await Promise.all([search(), loadMarket(), loadFilters()])
})
</script>

<template>
  <main class="shell">
    <header class="topbar">
      <a class="brand" href="#">
        <span class="brand-mark"><i></i><i></i><i></i></span>
        <span>就业雷达</span>
      </a>
      <nav><a class="active" href="#jobs">岗位市场</a><a href="#skills">技能信号</a><a href="#">我的画像</a></nav>
      <button class="profile-button">学生入口 <span>↗</span></button>
    </header>

    <section class="hero">
      <div class="hero-copy">
        <p class="eyebrow">高校智慧就业 · 实时岗位信号</p>
        <h1>找到下一份<br /><em>更合拍</em> 的工作</h1>
        <p class="hero-text">将你的能力、城市选择与真实市场需求放在同一张地图上，先看趋势，再做决定。</p>
        <div class="hero-actions"><a class="primary-action" href="#jobs">浏览岗位 <span>↓</span></a><span>来自 Spark 清洗后的三站岗位数据</span></div>
      </div>
      <div class="radar-card" aria-label="岗位市场雷达">
        <div class="radar-core"><strong>{{ headlineTotal }}</strong><small>已分析岗位</small></div>
        <span class="orbit orbit-one"></span><span class="orbit orbit-two"></span><span class="orbit orbit-three"></span>
        <span class="radar-dot dot-one"></span><span class="radar-dot dot-two"></span><span class="radar-dot dot-three"></span>
        <p class="radar-label label-top">需求上升<br /><b>大数据开发</b></p>
        <p class="radar-label label-right">热门城市<br /><b>成都 / 北京</b></p>
        <p class="radar-label label-bottom">技术密度<br /><b>Spark · SQL · Java</b></p>
      </div>
    </section>

    <section id="jobs" class="job-zone">
      <div class="section-head"><div><p class="eyebrow">01 / 市场岗位</p><h2>从市场里挑选方向</h2></div><p>筛选条件来自你的偏好，而不是一份冷冰冰的岗位清单。</p></div>
      <form class="filter-bar" @submit.prevent="search">
        <label class="search-field"><span>⌕</span><input v-model="keyword" placeholder="搜索岗位或公司" /></label>
        <div class="filter-picker" @focusout="activePicker = ''">
          <span class="picker-search-icon" aria-hidden="true">⌕</span>
          <input v-model="citySearch" class="picker-input" role="combobox" aria-label="搜索或选择城市" :aria-expanded="activePicker === 'city'" aria-controls="city-picker-options" autocomplete="off" placeholder="搜索城市" @focus="openPicker('city')" @input="updatePickerSearch('city')" @keydown="handlePickerKeydown('city', $event)" />
          <button class="picker-toggle" type="button" aria-label="展开城市选项" @mousedown.prevent @click="togglePicker('city')">⌄</button>
          <div v-if="activePicker === 'city'" id="city-picker-options" class="picker-menu" role="listbox" aria-label="城市匹配选项">
            <div class="picker-menu-head"><span>{{ matchingCities.length }} 个匹配城市</span><button type="button" @mousedown.prevent @click="clearPicker('city')">全部</button></div>
            <div class="picker-options"><button v-for="(item, index) in matchingCities" :key="item" class="picker-option" :class="{ active: index === activeOptionIndex, selected: item === city }" type="button" role="option" :aria-selected="item === city" @mousedown.prevent @click="choosePickerOption('city', item)">{{ item }}</button><p v-if="!matchingCities.length" class="picker-empty">没有匹配的城市</p></div>
          </div>
        </div>
        <div class="filter-picker" @focusout="activePicker = ''">
          <span class="picker-search-icon" aria-hidden="true">⌕</span>
          <input v-model="categorySearch" class="picker-input" role="combobox" aria-label="搜索或选择岗位方向" :aria-expanded="activePicker === 'category'" aria-controls="category-picker-options" autocomplete="off" placeholder="搜索方向" @focus="openPicker('category')" @input="updatePickerSearch('category')" @keydown="handlePickerKeydown('category', $event)" />
          <button class="picker-toggle" type="button" aria-label="展开岗位方向选项" @mousedown.prevent @click="togglePicker('category')">⌄</button>
          <div v-if="activePicker === 'category'" id="category-picker-options" class="picker-menu" role="listbox" aria-label="岗位方向匹配选项">
            <div class="picker-menu-head"><span>{{ matchingCategories.length }} 个匹配方向</span><button type="button" @mousedown.prevent @click="clearPicker('category')">全部</button></div>
            <div class="picker-options"><button v-for="(item, index) in matchingCategories" :key="item" class="picker-option" :class="{ active: index === activeOptionIndex, selected: item === category }" type="button" role="option" :aria-selected="item === category" @mousedown.prevent @click="choosePickerOption('category', item)">{{ item }}</button><p v-if="!matchingCategories.length" class="picker-empty">没有匹配的岗位方向</p></div>
          </div>
        </div>
        <button class="search-button" type="submit">更新结果</button><button class="reset-button" type="button" @click="reset">重置</button>
      </form>
      <p v-if="message" class="notice">{{ message }}</p>
      <div class="result-caption"><span>{{ loading ? '正在读取岗位…' : `发现 ${total.toLocaleString()} 个岗位机会` }}</span><span>{{ usingDemo ? 'DEMO MODE' : 'LIVE FROM MYSQL' }}</span></div>
      <div class="job-grid">
        <article v-for="job in jobs" :key="job.jobKey" class="job-card">
          <div class="card-top"><span class="category-tag">{{ job.jobCategory || '其他' }}</span><button aria-label="收藏岗位">＋</button></div>
          <h3>{{ job.jobName }}</h3><p class="company">{{ job.companyName }}</p>
          <p class="salary">{{ salary(job) }} <small>/ 月</small></p>
          <div class="facts"><span>⌖ {{ normalizeCity(job.city) }}</span><span>◫ {{ job.educationRequirement || '学历不限' }}</span><span>◌ {{ job.experienceRequirement || '经验不限' }}</span></div>
          <footer><span>{{ job.industry || '行业待补充' }}</span><a href="#">查看匹配 <b>→</b></a></footer>
        </article>
      </div>
    </section>

    <section id="skills" class="signal-zone">
      <div class="signal-copy"><p class="eyebrow">02 / 技能信号</p><h2>市场正在反复提及<br />这些能力。</h2><p>技能不是孤立的关键词。它们连接着岗位方向、城市机会和你的下一步练习。</p></div>
      <div class="stat-stack"><div class="stat-panel"><span>城市脉冲</span><ol><li v-for="(item, index) in cityStats.slice(0, 4)" :key="item.dimensionKey"><b>0{{ index + 1 }}</b><strong>{{ item.dimensionKey }}</strong><em>{{ Number(item.metricValue).toLocaleString() }}</em></li></ol></div><div class="skills-cloud"><span>高频技能</span><div><b v-for="item in hotSkills.slice(0, 6)" :key="item.dimensionKey">{{ item.dimensionKey }}</b></div></div></div>
    </section>
  </main>
</template>
