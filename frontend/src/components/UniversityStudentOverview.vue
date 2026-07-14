<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { AlertTriangle, CheckCircle2, ChevronLeft, ChevronRight, Clock3, RefreshCw, Search, UserRound } from '@lucide/vue'
import { apiRequest } from '../api/client'

const props = defineProps({ apiBase: { type: String, required: true }, initialPage: { type: Number, default: 1 } })
const emit = defineEmits(['page-change'])
const loading = ref(true)
const error = ref('')
const report = ref({ summary: {}, students: [], dataBasis: '', page: 1, size: 10, total: 0, totalPages: 1 })
const keyword = ref('')
const status = ref('all')
const selectedId = ref(null)
let searchTimer
const requestedPage = ref(props.initialPage)

const visibleStudents = computed(() => report.value.students || [])
const selected = computed(() => visibleStudents.value.find((student) => student.studentId === selectedId.value) || visibleStudents.value[0] || null)
const currentPage = computed(() => report.value.page || 1)
const totalPages = computed(() => report.value.totalPages || 1)
const filteredTotal = computed(() => report.value.total ?? visibleStudents.value.length)

async function load(page = 1) {
  requestedPage.value = page
  loading.value = true
  error.value = ''
  try {
    const params = new URLSearchParams({ page: String(page), size: '10', status: status.value })
    if (keyword.value.trim()) params.set('keyword', keyword.value.trim())
    report.value = await apiRequest(props.apiBase, `/university/students?${params}`)
    selectedId.value = report.value.students[0]?.studentId || null
  } catch (cause) {
    error.value = cause.message || '学生情况暂时无法读取'
  } finally {
    loading.value = false
  }
}

function selectStudent(student) { selectedId.value = student.studentId }
function setStatus(nextStatus) {
  if (status.value === nextStatus) return
  status.value = nextStatus
  emit('page-change', 1)
  load(1)
}
function changePage(nextPage) {
  if (nextPage < 1 || nextPage > totalPages.value || nextPage === currentPage.value || loading.value) return
  emit('page-change', nextPage)
  load(nextPage)
}
function scoreClass(score) {
  if (score >= 65) return 'strong'
  if (score >= 50) return 'medium'
  return 'weak'
}
function scoreText(student, field = 'topMatchScore') { return student?.bestJobName ? student[field] : '未计算' }
function matchPlaceholder(student) {
  if (!student.profileCompleted) return '画像尚未完善，暂不计算岗位匹配'
  if (!student.preferenceSaved) return '尚未填写就业期望，暂不计算岗位匹配'
  return '当前岗位批次暂无满足条件的匹配结果'
}
function formatTime(value) { return value ? new Date(value).toLocaleString('zh-CN', { hour12: false }) : '尚未保存' }

watch(keyword, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    emit('page-change', 1)
    load(1)
  }, 300)
})
watch(() => props.initialPage, (page) => {
  if (page !== requestedPage.value) load(page)
})
onBeforeUnmount(() => clearTimeout(searchTimer))
onMounted(() => load(props.initialPage))
</script>

<template>
  <section class="student-insight-page">
    <header class="student-insight-intro">
      <div><p class="eyebrow">学生情况</p><h2>优先跟进需要帮助的学生</h2></div>
      <button type="button" title="刷新学生情况" :disabled="loading" @click="load(currentPage)"><RefreshCw :size="17" /></button>
    </header>

    <div class="student-insight-summary" aria-label="学生情况汇总">
      <div><span>注册学生</span><strong>{{ report.summary.studentCount || 0 }}</strong></div>
      <div><span>已完善画像</span><strong>{{ report.summary.profileCompletedCount || 0 }}</strong></div>
      <div class="attention"><span>需重点关注</span><strong>{{ report.summary.difficultCount || 0 }}</strong></div>
      <div><span>本页平均匹配</span><strong>{{ report.summary.averageTopMatchScore || 0 }}<small> / 100</small></strong></div>
    </div>

    <div class="student-insight-controls">
      <label><Search :size="16" /><input v-model="keyword" aria-label="搜索学生" placeholder="搜索姓名、学号、学院或专业" /></label>
      <div role="group" aria-label="学生状态筛选"><button type="button" :class="{ active: status === 'all' }" @click="setStatus('all')">全部</button><button type="button" :class="{ active: status === 'difficult' }" @click="setStatus('difficult')">困难学生</button><button type="button" :class="{ active: status === 'normal' }" @click="setStatus('normal')">常规跟进</button></div>
    </div>

    <p v-if="error" class="student-insight-error">{{ error }}</p>

    <div class="student-insight-workbench" :class="{ loading }" :aria-busy="loading">
      <section class="student-attention-queue">
        <div class="insight-section-head"><span>学生队列</span><strong>共 {{ filteredTotal }} 人</strong></div>
        <button v-for="student in visibleStudents" :key="student.studentId" type="button" :class="{ selected: selected?.studentId === student.studentId, difficult: student.difficult }" @click="selectStudent(student)">
          <span class="student-avatar"><UserRound :size="16" /></span>
          <span class="student-identity"><strong>{{ student.name }}</strong><small>{{ student.studentNo }} · {{ student.major }}</small></span>
          <span class="student-state"><b>{{ student.status }}</b><small>{{ formatTime(student.lastSavedAt) }}</small></span>
          <span class="student-score" :class="student.bestJobName ? scoreClass(student.topMatchScore) : 'pending'">{{ scoreText(student) }}</span>
        </button>
        <p v-if="!visibleStudents.length" class="student-insight-empty">当前筛选下没有学生。</p>
        <footer v-if="totalPages > 1" class="student-list-pagination">
          <span>第 {{ currentPage }} / {{ totalPages }} 页</span>
          <div><button type="button" aria-label="上一页学生" :disabled="currentPage === 1 || loading" @click="changePage(currentPage - 1)"><ChevronLeft :size="16" /></button><button type="button" aria-label="下一页学生" :disabled="currentPage === totalPages || loading" @click="changePage(currentPage + 1)"><ChevronRight :size="16" /></button></div>
        </footer>
      </section>

      <aside v-if="selected" class="student-evidence-panel">
        <header><div><span>{{ selected.studentNo }}</span><h2>{{ selected.name }}</h2><p>{{ selected.college }} · {{ selected.major }} · {{ selected.education }}</p></div><span class="detail-status" :class="{ difficult: selected.difficult }"><AlertTriangle v-if="selected.difficult" :size="15" /><CheckCircle2 v-else :size="15" />{{ selected.status }}</span></header>
        <div class="student-evidence-metrics">
          <div><span>最佳匹配</span><strong :class="selected.bestJobName ? scoreClass(selected.topMatchScore) : 'pending'">{{ scoreText(selected) }}</strong></div>
          <div><span>Top5 平均</span><strong :class="{ pending: !selected.bestJobName }">{{ scoreText(selected, 'averageMatchScore') }}</strong></div>
          <div><span>技能 / 经历</span><strong>{{ selected.skillCount }} / {{ selected.experienceCount }}</strong></div>
        </div>
        <section class="best-match-line"><span>当前最匹配岗位</span><strong>{{ selected.bestJobName || matchPlaceholder(selected) }}</strong><small v-if="selected.bestJobCategory">{{ selected.bestJobCategory }}</small></section>
        <section class="student-gap-section"><div class="insight-section-head"><span>主要差距</span><strong>{{ selected.gaps?.length || 0 }} 项</strong></div><ul><li v-for="gap in selected.gaps || []" :key="gap"><AlertTriangle :size="14" />{{ gap }}</li><li v-if="!selected.gaps?.length"><CheckCircle2 :size="14" />当前没有明显短板</li></ul></section>
        <section class="student-evidence-section"><div class="insight-section-head"><span>已有证据</span><Clock3 :size="15" /></div><ul><li v-for="item in selected.evidence || []" :key="item">{{ item }}</li><li v-if="!selected.evidence?.length">学生尚未保存足够的画像证据。</li></ul></section>
        <footer><Clock3 :size="14" /><span>最后保存：{{ formatTime(selected.lastSavedAt) }}</span></footer>
      </aside>
      <aside v-else class="student-evidence-panel empty"><UserRound :size="24" /><p>当前页没有可展示的学生。</p></aside>
    </div>
  </section>
</template>
