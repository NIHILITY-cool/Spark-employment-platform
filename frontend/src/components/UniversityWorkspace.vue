<script setup>
import { computed, onMounted, ref } from 'vue'
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

async function loadAnalysis(resetSkills = false) {
  loading.value = true
  error.value = ''
  try {
    const params = new URLSearchParams({ major: major.value })
    if (city.value) params.set('city', city.value)
    analysis.value = await apiRequest(props.apiBase, `/university/training-alignment?${params}`)
    if (resetSkills || !selectedSkills.value.size) {
      const available = new Set(analysis.value.skills.map((item) => item.key))
      selectedSkills.value = new Set((presetSkills[major.value] || []).filter((item) => available.has(item)))
    }
  } catch (cause) {
    error.value = cause.message
  } finally {
    loading.value = false
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
