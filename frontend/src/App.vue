<script setup>
import { computed, defineAsyncComponent, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { ArrowDown, ArrowRight, ChevronLeft, ChevronRight, Clock3, Crosshair, GraduationCap, Heart, LogOut, MapPin, Search, Sparkles, UserRound } from '@lucide/vue'
import RoleLanding from './components/RoleLanding.vue'
import AuthGateway from './components/AuthGateway.vue'
import SearchSelect from './components/SearchSelect.vue'
import StudentWorkspace from './components/StudentWorkspace.vue'
import JobDetailDrawer from './components/JobDetailDrawer.vue'
import { apiRequest, authorizedFetch, clearAuthSession, getAuthSession, saveAuthSession } from './api/client'

const UniversityWorkspace = defineAsyncComponent(() => import('./components/UniversityWorkspace.vue'))
const StudentRegionPage = defineAsyncComponent(() => import('./components/StudentRegionPage.vue'))
const AdminWorkspace = defineAsyncComponent(() => import('./components/AdminWorkspace.vue'))

const apiBase = import.meta.env.VITE_API_BASE_URL || '/api'
const adminRoute = window.location.pathname.replace(/\/+$/, '') === '/admin'
const STUDENT_PATHS = {
  market: '/student/market',
  skills: '/student/skills',
  regions: '/student/regions',
  profile: '/student/profile',
  recommendations: '/student/recommendations',
}
const UNIVERSITY_TABS = new Set(['overview', 'demand', 'region', 'salary', 'training', 'students'])
let historyIndex = 0
const authReady = ref(false)
const authAccount = ref(null)
const authRole = ref('STUDENT')
const loading = ref(false)
const usingDemo = ref(false)
const message = ref('')
const keyword = ref('')
const city = ref('')
const category = ref('')
const jobs = ref([])
const total = ref(0)
const jobPage = ref(1)
const hotSkills = ref([])
const cityOptions = ref([])
const categoryOptions = ref([])
const view = ref('landing')
const studentTab = ref('profile')
const universityTab = ref('overview')
const universityStudentPage = ref(1)
const favorites = ref(new Set(JSON.parse(localStorage.getItem('favoriteJobs') || '[]')))
const selectedSkill = ref('')
const skillPage = ref(1)
const activeJobDetail = ref(null)
const jobDetailLoading = ref(false)
const jobDetailError = ref('')

const JOBS_PER_PAGE = 12
const SKILLS_PER_PAGE = 8

const demoJobs = [
  { jobKey: 'ncss-demo-1', jobName: '大数据开发工程师', companyName: '华川数智科技', city: '成都', jobCategory: '大数据开发', salaryMin: 9000, salaryMax: 14000, educationRequirement: '本科及以上', experienceRequirement: '经验不限', industry: '计算机软件' },
  { jobKey: 'liepin-demo-2', jobName: '数据分析师', companyName: '西南云图信息', city: '重庆', jobCategory: '数据分析', salaryMin: 8000, salaryMax: 13000, educationRequirement: '本科', experienceRequirement: '1-3年', industry: '互联网/电子商务' },
  { jobKey: 'guopin-demo-3', jobName: 'Java 后端开发工程师', companyName: '国创智联', city: '北京', jobCategory: '后端开发', salaryMin: 11000, salaryMax: 18000, educationRequirement: '本科及以上', experienceRequirement: '经验不限', industry: '软件和信息技术服务业' },
]

const demoCities = [...new Set(demoJobs.map((job) => job.city))]
const demoCategories = [...new Set(demoJobs.map((job) => job.jobCategory))]
const headlineTotal = computed(() => (total.value || 11559).toLocaleString())
const skillSignals = computed(() => {
  const ordered = [...hotSkills.value].sort((a, b) => Number(b.metricValue) - Number(a.metricValue))
  const peak = Math.max(1, ...ordered.map((item) => Number(item.metricValue || 0)))
  return ordered.map((item, index) => ({
    name: item.dimensionKey,
    mentions: Number(item.metricValue || 0),
    rank: index + 1,
    strength: Math.max(4, Math.round(Number(item.metricValue || 0) / peak * 100)),
  }))
})
const skillMentionTotal = computed(() => skillSignals.value.reduce((sum, item) => sum + item.mentions, 0))
const focusedSkill = computed(() => skillSignals.value.find((item) => item.name === selectedSkill.value) || skillSignals.value[0])
const jobPageCount = computed(() => Math.max(1, Math.ceil(total.value / JOBS_PER_PAGE)))
const skillPageCount = computed(() => Math.max(1, Math.ceil(skillSignals.value.length / SKILLS_PER_PAGE)))
const visibleSkillSignals = computed(() => skillSignals.value.slice((skillPage.value - 1) * SKILLS_PER_PAGE, skillPage.value * SKILLS_PER_PAGE))
const jobPageItems = computed(() => pageItems(jobPage.value, jobPageCount.value))
const skillPageItems = computed(() => pageItems(skillPage.value, skillPageCount.value))

function normalizePathname(pathname = window.location.pathname) {
  const normalized = pathname.replace(/\/+$/, '')
  return normalized || '/'
}

function readRoute() {
  const pathname = normalizePathname()
  const params = new URLSearchParams(window.location.search)
  if (pathname === '/login/student') return { view: 'auth', role: 'STUDENT' }
  if (pathname === '/login/university') return { view: 'auth', role: 'UNIVERSITY' }
  if (pathname === STUDENT_PATHS.market) {
    return {
      view: 'market',
      jobPage: Math.max(1, Number(params.get('page')) || 1),
      keyword: params.get('keyword') || '', city: params.get('city') || '', category: params.get('category') || '',
    }
  }
  if (pathname === STUDENT_PATHS.skills) return { view: 'skills', skillPage: Math.max(1, Number(params.get('page')) || 1) }
  if (pathname === STUDENT_PATHS.regions) return { view: 'regions' }
  if (pathname === STUDENT_PATHS.profile) return { view: 'student', studentTab: 'profile' }
  if (pathname === STUDENT_PATHS.recommendations) return { view: 'student', studentTab: 'recommendations' }
  if (pathname === '/university') {
    const tab = params.get('tab')
    const universityTab = UNIVERSITY_TABS.has(tab) ? tab : 'overview'
    return {
      view: 'university', universityTab,
      universityStudentPage: universityTab === 'students' ? Math.max(1, Number(params.get('page')) || 1) : 1,
    }
  }
  return { view: 'landing' }
}

function isStudentView(nextView) {
  return ['market', 'skills', 'regions', 'student'].includes(nextView)
}

function pathForRoute(route) {
  if (route.view === 'auth') return route.role === 'UNIVERSITY' ? '/login/university' : '/login/student'
  if (route.view === 'market') {
    const params = new URLSearchParams()
    if (jobPage.value > 1) params.set('page', String(jobPage.value))
    if (keyword.value.trim()) params.set('keyword', keyword.value.trim())
    if (city.value) params.set('city', city.value)
    if (category.value) params.set('category', category.value)
    const query = params.toString()
    return `${STUDENT_PATHS.market}${query ? `?${query}` : ''}`
  }
  if (route.view === 'skills') return `${STUDENT_PATHS.skills}${skillPage.value > 1 ? `?page=${skillPage.value}` : ''}`
  if (route.view === 'regions') return STUDENT_PATHS.regions
  if (route.view === 'student') return STUDENT_PATHS[route.studentTab || studentTab.value] || STUDENT_PATHS.profile
  if (route.view === 'university') {
    const params = new URLSearchParams()
    if (universityTab.value !== 'overview') params.set('tab', universityTab.value)
    if (universityTab.value === 'students' && universityStudentPage.value > 1) params.set('page', String(universityStudentPage.value))
    const query = params.toString()
    return `/university${query ? `?${query}` : ''}`
  }
  return '/'
}

function applyRoute(route) {
  view.value = route.view
  if (route.role) authRole.value = route.role
  if (route.studentTab) studentTab.value = route.studentTab
  if (route.universityTab) universityTab.value = route.universityTab
  if ('universityStudentPage' in route) universityStudentPage.value = route.universityStudentPage
  if (route.view === 'market') {
    if ('keyword' in route) keyword.value = route.keyword
    if ('city' in route) city.value = route.city
    if ('category' in route) category.value = route.category
    if ('jobPage' in route) jobPage.value = route.jobPage
  }
  if (route.view === 'skills') skillPage.value = route.skillPage || 1
}

function replaceLocation(route = readRoute()) {
  const path = pathForRoute(route)
  if (`${window.location.pathname}${window.location.search}` !== path) {
    window.history.replaceState({ employmentRoute: true, index: historyIndex }, '', path)
  }
}

function navigate(route, { replace = false, scroll = true } = {}) {
  applyRoute(route)
  const path = pathForRoute(route)
  if (`${window.location.pathname}${window.location.search}` !== path) {
    if (replace) window.history.replaceState({ employmentRoute: true, index: historyIndex }, '', path)
    else {
      historyIndex += 1
      window.history.pushState({ employmentRoute: true, index: historyIndex }, '', path)
    }
  }
  if (scroll) nextTick(() => window.scrollTo({ top: 0, behavior: 'auto' }))
}

function initializeHistory() {
  const state = window.history.state
  if (state?.employmentRoute) historyIndex = Number(state.index) || 0
  else window.history.replaceState({ employmentRoute: true, index: historyIndex }, '', `${window.location.pathname}${window.location.search}`)
}

function handlePopState(event) {
  historyIndex = Number(event.state?.index) || 0
  applyRoute(readRoute())
  void reconcileRoute()
}

function salary(job) {
  if (!job.salaryMin || !job.salaryMax) return '薪资面议'
  return `${Math.round(job.salaryMin / 1000)}K–${Math.round(job.salaryMax / 1000)}K`
}

function normalizeCity(value) {
  const normalized = String(value || '').trim().replace(/市+$/, '')
  return normalized === '中国' ? '全国' : normalized
}

function pageItems(current, count) {
  if (count <= 7) return Array.from({ length: count }, (_, index) => index + 1)
  if (current <= 4) return [1, 2, 3, 4, 5, 'ellipsis-right', count]
  if (current >= count - 3) return [1, 'ellipsis-left', count - 4, count - 3, count - 2, count - 1, count]
  return [1, 'ellipsis-left', current - 1, current, current + 1, 'ellipsis-right', count]
}

async function loadMarket() {
  try {
    const skillResponse = await authorizedFetch(`${apiBase}/market/statistics/hot_skills`)
    if (!skillResponse.ok) throw new Error('market unavailable')
    hotSkills.value = await skillResponse.json()
    if (!selectedSkill.value || !hotSkills.value.some((item) => item.dimensionKey === selectedSkill.value)) selectedSkill.value = hotSkills.value[0]?.dimensionKey || ''
  } catch {
    hotSkills.value = [
      { dimensionKey: 'Python', metricValue: 841 }, { dimensionKey: 'Java', metricValue: 782 },
      { dimensionKey: 'SQL', metricValue: 669 }, { dimensionKey: 'Spark', metricValue: 315 },
    ]
    if (!selectedSkill.value) selectedSkill.value = hotSkills.value[0]?.dimensionKey || ''
  }
}

async function loadFilters() {
  try {
    const response = await authorizedFetch(`${apiBase}/jobs/filters`)
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

async function search(requestedPage = 1) {
  loading.value = true
  message.value = ''
  const requested = Math.max(Number(requestedPage) || 1, 1)
  const safePage = total.value ? Math.min(requested, jobPageCount.value) : requested
  const params = new URLSearchParams({ page: String(safePage), size: String(JOBS_PER_PAGE) })
  if (keyword.value.trim()) params.set('keyword', keyword.value.trim())
  if (city.value) params.set('city', city.value)
  if (category.value) params.set('category', category.value)
  try {
    const response = await authorizedFetch(`${apiBase}/jobs?${params}`)
    if (!response.ok) throw new Error('jobs unavailable')
    const payload = await response.json()
    jobs.value = payload.records
    total.value = payload.total
    jobPage.value = payload.page
    usingDemo.value = false
  } catch {
    jobs.value = demoJobs.filter((job) => (!city.value || job.city === city.value) && (!category.value || job.jobCategory === category.value) && (!keyword.value || `${job.jobName}${job.companyName}`.includes(keyword.value)))
    total.value = jobs.value.length
    jobPage.value = 1
    usingDemo.value = true
    message.value = '当前显示演示数据：本机前端已启动，等待虚拟机后端服务开放后将自动读取真实岗位。'
  } finally {
    loading.value = false
    if (view.value === 'market') replaceLocation({ view: 'market' })
  }
}

function changeJobPage(page) {
  if (page < 1 || page > jobPageCount.value || page === jobPage.value || loading.value) return
  search(page)
}

function changeSkillPage(page) {
  if (page < 1 || page > skillPageCount.value || page === skillPage.value) return
  skillPage.value = page
  if (!visibleSkillSignals.value.some((item) => item.name === selectedSkill.value)) selectedSkill.value = visibleSkillSignals.value[0]?.name || ''
  replaceLocation({ view: 'skills' })
}

function reset() {
  keyword.value = ''
  city.value = ''
  category.value = ''
  search(1)
}

function openStudent(tab = 'profile') {
  navigate({ view: 'student', studentTab: tab })
}

function setStudentTab(tab) {
  if (!['profile', 'recommendations'].includes(tab) || tab === studentTab.value) return
  navigate({ view: 'student', studentTab: tab })
}

function setUniversityTab(tab) {
  if (!UNIVERSITY_TABS.has(tab) || tab === universityTab.value) return
  navigate({ view: 'university', universityTab: tab })
}

function setUniversityStudentPage(page) {
  if (universityTab.value !== 'students' || page === universityStudentPage.value) return
  navigate({ view: 'university', universityTab: 'students', universityStudentPage: page }, { replace: true, scroll: false })
}

function enterStudent() {
  if (authAccount.value?.role === 'STUDENT') showMarket()
  else navigate({ view: 'auth', role: 'STUDENT' })
}

function enterUniversity() {
  if (authAccount.value?.role === 'UNIVERSITY') navigate({ view: 'university', universityTab: 'overview' })
  else navigate({ view: 'auth', role: 'UNIVERSITY' })
}

function showPortal() {
  if (view.value === 'auth' && historyIndex > 0) window.history.back()
  else navigate({ view: 'landing' }, { replace: view.value === 'auth' })
}

async function handleAuthenticated(session) {
  saveAuthSession(session)
  authAccount.value = session.account
  if (session.account.role === 'STUDENT') {
    await Promise.all([search(1), loadMarket(), loadFilters()])
    navigate({ view: 'market' }, { replace: true })
  } else if (session.account.role === 'UNIVERSITY') {
    await loadFilters()
    navigate({ view: 'university', universityTab: 'overview' }, { replace: true })
  }
}

async function logout() {
  try { await apiRequest(apiBase, '/auth/logout', { method: 'POST' }) } catch { /* Session may already be expired. */ }
  clearAuthSession()
  authAccount.value = null
  jobs.value = []
  total.value = 0
  navigate({ view: 'landing' }, { replace: true })
}

function showMarket(anchor = '') {
  const changingView = view.value !== 'market'
  navigate({ view: 'market' }, { scroll: changingView && !anchor })
  nextTick(() => {
    if (anchor) document.querySelector(anchor)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  })
}

function showSkills() {
  navigate({ view: 'skills' })
  if (!selectedSkill.value) selectedSkill.value = skillSignals.value[0]?.name || ''
}

function showRegions() {
  navigate({ view: 'regions' })
}

function browseCityJobs(cityName) {
  city.value = cityName
  navigate({ view: 'market' }, { scroll: false })
  nextTick(() => {
    search(1)
    document.querySelector('#jobs')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  })
}

function toggleFavorite(jobKey) {
  const next = new Set(favorites.value)
  if (next.has(jobKey)) next.delete(jobKey)
  else next.add(jobKey)
  favorites.value = next
  localStorage.setItem('favoriteJobs', JSON.stringify([...next]))
}

async function openJobDetail(job) {
  activeJobDetail.value = { job, skills: [] }
  jobDetailLoading.value = true
  jobDetailError.value = ''
  try {
    const response = await authorizedFetch(`${apiBase}/jobs/${encodeURIComponent(job.jobKey)}`)
    if (!response.ok) throw new Error('暂时无法读取岗位完整信息')
    const payload = await response.json()
    if (activeJobDetail.value?.job?.jobKey === job.jobKey) activeJobDetail.value = payload
  } catch (error) {
    jobDetailError.value = error.message || '暂时无法读取岗位完整信息'
  } finally {
    jobDetailLoading.value = false
  }
}

function closeJobDetail() {
  activeJobDetail.value = null
  jobDetailError.value = ''
}

function handleGlobalKeydown(event) {
  if (event.key === 'Escape' && activeJobDetail.value) closeJobDetail()
}

async function bootstrapAuth() {
  if (adminRoute) {
    authReady.value = true
    return
  }
  applyRoute(readRoute())
  const session = getAuthSession()
  if (!session?.token) {
    authReady.value = true
    await reconcileRoute()
    return
  }
  try {
    const account = await apiRequest(apiBase, '/auth/me')
    authAccount.value = account
    if (account.role === 'STUDENT') {
      const route = readRoute()
      await Promise.all([search(route.view === 'market' ? route.jobPage : 1), loadMarket(), loadFilters()])
    } else if (account.role === 'UNIVERSITY') {
      await loadFilters()
    } else {
      clearAuthSession()
      authAccount.value = null
    }
  } catch {
    clearAuthSession()
    authAccount.value = null
  } finally {
    authReady.value = true
    await reconcileRoute()
  }
}

async function reconcileRoute() {
  if (adminRoute || !authReady.value) return
  const route = readRoute()
  const account = authAccount.value
  if (!account) {
    if (isStudentView(route.view)) navigate({ view: 'auth', role: 'STUDENT' }, { replace: true, scroll: false })
    else if (route.view === 'university') navigate({ view: 'auth', role: 'UNIVERSITY' }, { replace: true, scroll: false })
    else applyRoute(route)
    return
  }

  if (account.role === 'STUDENT') {
    if (!isStudentView(route.view)) navigate({ view: 'market' }, { replace: true, scroll: false })
    else applyRoute(route)
    return
  }

  if (account.role === 'UNIVERSITY') {
    if (route.view !== 'university') navigate({ view: 'university', universityTab: 'overview' }, { replace: true, scroll: false })
    else applyRoute(route)
  }
}

onMounted(async () => {
  initializeHistory()
  window.addEventListener('keydown', handleGlobalKeydown)
  window.addEventListener('popstate', handlePopState)
  await bootstrapAuth()
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleGlobalKeydown)
  window.removeEventListener('popstate', handlePopState)
})
</script>

<template>
  <AdminWorkspace v-if="adminRoute" :api-base="apiBase" />
  <main v-else class="shell" :class="{ 'portal-shell': ['landing', 'auth'].includes(view) }">
    <div v-if="!authReady" class="auth-bootstrap">正在恢复登录状态…</div>

    <RoleLanding v-else-if="view === 'landing'" :job-count="headlineTotal" @select-student="enterStudent" @select-university="enterUniversity" />

    <AuthGateway v-else-if="view === 'auth'" :api-base="apiBase" :role="authRole" @authenticated="handleAuthenticated" @back="showPortal" />

    <UniversityWorkspace v-else-if="view === 'university'" :api-base="apiBase" :city-options="cityOptions" :initial-tab="universityTab" :initial-student-page="universityStudentPage" @student-page-change="setUniversityStudentPage" @tab-change="setUniversityTab" @logout="logout" />

    <template v-else>
    <header class="topbar">
      <button class="brand" type="button" @click="showMarket()">
        <span class="brand-mark"><i></i><i></i><i></i></span>
        <span>就业雷达</span>
      </button>
      <nav>
        <button :class="{ active: view === 'market' }" type="button" @click="showMarket('#jobs')">岗位市场</button>
        <button :class="{ active: view === 'regions' }" type="button" @click="showRegions">地区分布</button>
        <button :class="{ active: view === 'skills' }" type="button" @click="showSkills">技能信号</button>
        <button :class="{ active: view === 'student' }" type="button" @click="openStudent('profile')">我的画像</button>
      </nav>
      <div class="top-actions">
        <button class="university-button" type="button" title="退出学生端" @click="logout"><LogOut :size="15" /><span>退出登录</span></button>
        <button class="profile-button" type="button" @click="openStudent('recommendations')"><UserRound :size="15" />我的工作台<ArrowRight :size="15" /></button>
      </div>
    </header>
    <div class="student-mobile-nav" role="tablist" aria-label="学生端页面">
      <button :class="{ active: view === 'market' }" type="button" role="tab" :aria-selected="view === 'market'" @click="showMarket()">岗位市场</button>
      <button :class="{ active: view === 'regions' }" type="button" role="tab" :aria-selected="view === 'regions'" @click="showRegions">地区分布</button>
      <button :class="{ active: view === 'skills' }" type="button" role="tab" :aria-selected="view === 'skills'" @click="showSkills">技能信号</button>
      <button :class="{ active: view === 'student' }" type="button" role="tab" :aria-selected="view === 'student'" @click="openStudent('profile')">我的画像</button>
    </div>

    <template v-if="view === 'market'">
    <section class="hero">
      <div class="hero-copy">
        <p class="eyebrow">就业市场 · 近期岗位</p>
        <h1>找到下一份<br /><em>更合拍</em> 的工作</h1>
        <p class="hero-text">将你的能力、城市选择与真实市场需求放在同一张地图上，先看趋势，再做决定。</p>
        <div class="hero-actions"><button class="primary-action" type="button" @click="showMarket('#jobs')">浏览岗位 <ArrowDown :size="16" /></button><span>{{ headlineTotal }} 个近期岗位</span></div>
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
      <div class="section-head"><div><p class="eyebrow">市场岗位</p><h2>从市场里挑选方向</h2></div><p>按城市和岗位方向缩小范围。</p></div>
      <form class="filter-bar" @submit.prevent="search(1)">
        <label class="search-field"><Search :size="18" /><input v-model="keyword" placeholder="搜索岗位或公司" /></label>
        <SearchSelect v-model="city" class="filter-picker" label="搜索或选择城市" placeholder="搜索城市" empty-label="全部城市" :options="cityOptions" />
        <SearchSelect v-model="category" class="filter-picker" label="搜索或选择岗位方向" placeholder="搜索方向" empty-label="全部方向" :options="categoryOptions" />
        <button class="search-button" type="submit">更新结果</button><button class="reset-button" type="button" @click="reset">重置</button>
      </form>
      <p v-if="message" class="notice">{{ message }}</p>
      <div class="result-caption"><span>{{ loading ? '正在读取岗位…' : `发现 ${total.toLocaleString()} 个岗位机会` }}</span><span>{{ usingDemo ? '示例数据' : '当前筛选' }}</span></div>
      <div class="job-grid">
        <article v-for="job in jobs" :key="job.jobKey" class="job-card job-card-clickable" role="button" tabindex="0" :aria-label="`查看${job.jobName}岗位详情`" @click="openJobDetail(job)" @keydown.enter="openJobDetail(job)" @keydown.space.prevent="openJobDetail(job)">
          <div class="card-top"><span class="category-tag">{{ job.jobCategory || '其他' }}</span><button type="button" :class="{ saved: favorites.has(job.jobKey) }" :aria-label="favorites.has(job.jobKey) ? '取消收藏岗位' : '收藏岗位'" :aria-pressed="favorites.has(job.jobKey)" :title="favorites.has(job.jobKey) ? '取消收藏' : '收藏岗位'" @click.stop="toggleFavorite(job.jobKey)"><Heart :size="18" :fill="favorites.has(job.jobKey) ? 'currentColor' : 'none'" /></button></div>
          <h3>{{ job.jobName }}</h3><p class="company">{{ job.companyName }}</p>
          <p class="salary">{{ salary(job) }} <small>/ 月</small></p>
          <div class="facts"><span><MapPin :size="13" />{{ normalizeCity(job.city) }}</span><span><GraduationCap :size="13" />{{ job.educationRequirement || '学历不限' }}</span><span><Clock3 :size="13" />{{ job.experienceRequirement || '经验不限' }}</span></div>
          <footer><span>{{ job.industry || '行业待补充' }}</span><span class="job-card-open-hint" aria-hidden="true"><ArrowRight :size="17" /></span></footer>
        </article>
      </div>
      <nav v-if="jobPageCount > 1" class="data-pagination" aria-label="岗位分页">
        <button type="button" class="pagination-step" :disabled="jobPage === 1 || loading" aria-label="上一页岗位" @click="changeJobPage(jobPage - 1)"><ChevronLeft :size="16" /></button>
        <template v-for="item in jobPageItems" :key="item">
          <span v-if="typeof item !== 'number'" class="pagination-ellipsis" aria-hidden="true">···</span>
          <button v-else type="button" class="pagination-number" :class="{ active: item === jobPage }" :aria-current="item === jobPage ? 'page' : undefined" @click="changeJobPage(item)">{{ item }}</button>
        </template>
        <button type="button" class="pagination-step" :disabled="jobPage === jobPageCount || loading" aria-label="下一页岗位" @click="changeJobPage(jobPage + 1)"><ChevronRight :size="16" /></button>
        <span class="pagination-summary">第 {{ jobPage }} / {{ jobPageCount }} 页</span>
      </nav>
    </section>

    </template>

    <template v-else-if="view === 'skills'">
      <section class="skills-page">
        <header class="skills-page-banner">
          <div>
            <p class="eyebrow">市场技能信号 · 近期公开岗位</p>
            <h1>把市场语言<br />拆成可行动的技能。</h1>
            <p>比较近期岗位中的技能需求，确定更值得优先投入的学习方向。</p>
          </div>
          <div class="skills-highlights" aria-label="技能信号摘要">
            <div><span>高频技能</span><strong>{{ skillSignals[0]?.name || '暂无' }}</strong></div>
            <div><span>技能提及</span><strong>{{ skillMentionTotal.toLocaleString() }}</strong></div>
            <div><span>有效信号</span><strong>{{ skillSignals.length }}</strong></div>
          </div>
        </header>

        <div class="skills-analytics">
          <section class="skills-ranking">
            <div class="skills-page-head"><div><p class="eyebrow">需求强度</p><h2>市场技能排名</h2></div><span>每页 {{ SKILLS_PER_PAGE }} 项 · 点击一项查看重点</span></div>
            <div class="skill-signal-list">
              <button v-for="skill in visibleSkillSignals" :key="skill.name" class="skill-signal" :class="{ selected: focusedSkill?.name === skill.name }" type="button" :aria-pressed="focusedSkill?.name === skill.name" @click="selectedSkill = skill.name">
                <span class="skill-signal-rank">{{ String(skill.rank).padStart(2, '0') }}</span><strong>{{ skill.name }}</strong><i><b :style="{ width: `${skill.strength}%` }"></b></i><em>{{ skill.mentions.toLocaleString() }}</em>
              </button>
            </div>
            <nav v-if="skillPageCount > 1" class="data-pagination skills-pagination" aria-label="技能信号分页">
              <button type="button" class="pagination-step" :disabled="skillPage === 1" aria-label="上一页技能信号" @click="changeSkillPage(skillPage - 1)"><ChevronLeft :size="16" /></button>
              <template v-for="item in skillPageItems" :key="item">
                <span v-if="typeof item !== 'number'" class="pagination-ellipsis" aria-hidden="true">···</span>
                <button v-else type="button" class="pagination-number" :class="{ active: item === skillPage }" :aria-current="item === skillPage ? 'page' : undefined" @click="changeSkillPage(item)">{{ item }}</button>
              </template>
              <button type="button" class="pagination-step" :disabled="skillPage === skillPageCount" aria-label="下一页技能信号" @click="changeSkillPage(skillPage + 1)"><ChevronRight :size="16" /></button>
              <span class="pagination-summary">第 {{ skillPage }} / {{ skillPageCount }} 页</span>
            </nav>
          </section>

          <aside class="skill-focus-panel">
            <p class="eyebrow"><Crosshair :size="14" />当前聚焦</p>
            <h2>{{ focusedSkill?.name || '暂无技能' }}</h2>
            <p>将该技能与岗位方向、项目经历一起维护，推荐结果才会更接近你的真实准备度。</p>
            <div class="focus-metric"><strong>{{ focusedSkill?.mentions?.toLocaleString() || '0' }}</strong><span>岗位提及</span><small>近期公开岗位样本</small></div>
            <button class="command secondary" type="button" @click="openStudent('profile')"><Sparkles :size="16" />校准我的技能画像</button>
          </aside>
        </div>

      </section>
    </template>

    <StudentRegionPage v-else-if="view === 'regions'" :api-base="apiBase" @browse-city="browseCityJobs" />

    <StudentWorkspace v-else :api-base="apiBase" :student-id="authAccount.studentId" :city-options="cityOptions" :category-options="categoryOptions" :initial-tab="studentTab" @back-to-market="showMarket()" @tab-change="setStudentTab" />
    </template>

    <JobDetailDrawer :detail="activeJobDetail" :loading="jobDetailLoading" :error="jobDetailError" @close="closeJobDetail" />
  </main>
</template>
