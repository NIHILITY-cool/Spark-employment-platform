<script setup>
import { computed, onMounted, ref } from 'vue'
import { AlertTriangle, CheckCircle2, Clock3, RefreshCw, Search, UserRound } from '@lucide/vue'
import { apiRequest } from '../api/client'

const props = defineProps({ apiBase: { type: String, required: true } })

const loading = ref(true)
const error = ref('')
const report = ref({ summary: {}, students: [], dataBasis: '' })
const keyword = ref('')
const status = ref('all')
const selectedId = ref(null)

const visibleStudents = computed(() => report.value.students.filter((student) => {
  const text = `${student.name}${student.studentNo}${student.college}${student.major}`.toLowerCase()
  const matchesKeyword = !keyword.value.trim() || text.includes(keyword.value.trim().toLowerCase())
  const matchesStatus = status.value === 'all' || (status.value === 'difficult' ? student.difficult : !student.difficult)
  return matchesKeyword && matchesStatus
}))
const selected = computed(() => report.value.students.find((student) => student.studentId === selectedId.value)
  || visibleStudents.value[0] || null)

async function load() {
  loading.value = true
  error.value = ''
  try {
    report.value = await apiRequest(props.apiBase, '/university/students')
    selectedId.value = report.value.students[0]?.studentId || null
  } catch (cause) {
    error.value = cause.message || '学生情况暂时无法读取'
  } finally {
    loading.value = false
  }
}

function selectStudent(student) {
  selectedId.value = student.studentId
}

function scoreClass(score) {
  if (score >= 65) return 'strong'
  if (score >= 50) return 'medium'
  return 'weak'
}

function formatTime(value) {
  return value ? new Date(value).toLocaleString('zh-CN', { hour12: false }) : '尚未保存'
}

onMounted(load)
</script>

<template>
  <section class="student-insight-page">
    <header class="student-insight-intro">
      <div><p class="eyebrow">学生情况</p><h2>优先跟进需要帮助的学生</h2></div>
      <button type="button" title="刷新学生情况" :disabled="loading" @click="load"><RefreshCw :size="17" /></button>
    </header>

    <div class="student-insight-summary" aria-label="学生情况汇总">
      <div><span>注册学生</span><strong>{{ report.summary.studentCount || 0 }}</strong></div>
      <div><span>已完善画像</span><strong>{{ report.summary.profileCompletedCount || 0 }}</strong></div>
      <div class="attention"><span>需重点关注</span><strong>{{ report.summary.difficultCount || 0 }}</strong></div>
      <div><span>平均最佳匹配</span><strong>{{ report.summary.averageTopMatchScore || 0 }}<small> / 100</small></strong></div>
    </div>

    <div class="student-insight-controls">
      <label><Search :size="16" /><input v-model="keyword" placeholder="搜索姓名、学号、学院或专业" /></label>
      <div role="group" aria-label="学生状态筛选"><button type="button" :class="{ active: status === 'all' }" @click="status = 'all'">全部</button><button type="button" :class="{ active: status === 'difficult' }" @click="status = 'difficult'">困难学生</button><button type="button" :class="{ active: status === 'normal' }" @click="status = 'normal'">常规跟进</button></div>
    </div>

    <p v-if="error" class="student-insight-error">{{ error }}</p>
    <div v-if="loading" class="student-insight-loading">正在读取学生最后保存的状态…</div>

    <div v-else class="student-insight-workbench">
      <section class="student-attention-queue">
        <div class="insight-section-head"><span>学生队列</span><strong>{{ visibleStudents.length }} 人</strong></div>
        <button v-for="student in visibleStudents" :key="student.studentId" type="button" :class="{ selected: selected?.studentId === student.studentId, difficult: student.difficult }" @click="selectStudent(student)">
          <span class="student-avatar"><UserRound :size="16" /></span>
          <span class="student-identity"><strong>{{ student.name }}</strong><small>{{ student.studentNo }} · {{ student.major }}</small></span>
          <span class="student-state"><b>{{ student.status }}</b><small>{{ formatTime(student.lastSavedAt) }}</small></span>
          <span class="student-score" :class="scoreClass(student.topMatchScore)">{{ student.topMatchScore || '-' }}</span>
        </button>
        <p v-if="!visibleStudents.length" class="student-insight-empty">当前筛选下没有学生。</p>
      </section>

      <aside v-if="selected" class="student-evidence-panel">
        <header>
          <div><span>{{ selected.studentNo }}</span><h2>{{ selected.name }}</h2><p>{{ selected.college }} · {{ selected.major }} · {{ selected.education }}</p></div>
          <span class="detail-status" :class="{ difficult: selected.difficult }"><AlertTriangle v-if="selected.difficult" :size="15" /><CheckCircle2 v-else :size="15" />{{ selected.status }}</span>
        </header>

        <div class="student-evidence-metrics">
          <div><span>最佳匹配</span><strong :class="scoreClass(selected.topMatchScore)">{{ selected.topMatchScore || '-' }}</strong></div>
          <div><span>Top5 平均</span><strong>{{ selected.averageMatchScore || '-' }}</strong></div>
          <div><span>技能 / 经历</span><strong>{{ selected.skillCount }} / {{ selected.experienceCount }}</strong></div>
        </div>

        <section class="best-match-line">
          <span>当前最匹配岗位</span><strong>{{ selected.bestJobName || '画像或就业期望尚不足以计算' }}</strong><small v-if="selected.bestJobCategory">{{ selected.bestJobCategory }}</small>
        </section>

        <section class="student-gap-section">
          <div class="insight-section-head"><span>主要差距</span><strong>{{ selected.gaps.length }} 项</strong></div>
          <ul><li v-for="gap in selected.gaps" :key="gap"><AlertTriangle :size="14" />{{ gap }}</li><li v-if="!selected.gaps.length"><CheckCircle2 :size="14" />当前没有明显短板</li></ul>
        </section>

        <section class="student-evidence-section">
          <div class="insight-section-head"><span>已有证据</span><Clock3 :size="15" /></div>
          <ul><li v-for="item in selected.evidence" :key="item">{{ item }}</li><li v-if="!selected.evidence.length">学生尚未保存足够的画像证据。</li></ul>
        </section>

        <footer><Clock3 :size="14" /><span>最后保存：{{ formatTime(selected.lastSavedAt) }}</span></footer>
      </aside>
      <aside v-else class="student-evidence-panel empty"><UserRound :size="24" /><p>选择一名学生查看匹配和差距。</p></aside>
    </div>
  </section>
</template>
