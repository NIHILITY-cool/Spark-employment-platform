<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import {
  ArrowLeft,
  ArrowRight,
  BookOpenCheck,
  BriefcaseBusiness,
  Check,
  ChevronDown,
  CircleAlert,
  ExternalLink,
  GraduationCap,
  Lightbulb,
  LoaderCircle,
  MapPin,
  Plus,
  RefreshCw,
  Save,
  Sparkles,
  Target,
  Trash2,
  UserRound,
  WalletCards,
  X,
} from '@lucide/vue'
import { apiRequest } from '../api/client'
import SearchSelect from './SearchSelect.vue'

const props = defineProps({
  apiBase: { type: String, required: true },
  studentId: { type: Number, default: 1 },
  cityOptions: { type: Array, default: () => [] },
  categoryOptions: { type: Array, default: () => [] },
  initialTab: { type: String, default: 'profile' },
})

const emit = defineEmits(['back-to-market'])

const activeTab = ref(props.initialTab)
const loading = ref(true)
const saving = ref('')
const error = ref('')
const notice = ref('')
const expandedJob = ref('')
const profile = reactive({
  studentNo: '', name: '', college: '', major: '', education: '', graduationYear: 2027,
})
const preference = reactive({
  expectedJob: '', expectedCity: '', expectedIndustry: '', salaryMin: 0, salaryMax: 0,
  acceptRemoteCity: true,
})
const skills = ref([])
const recommendations = ref([])
const skillGap = ref(null)
const newSkill = reactive({ skillName: '', skillLevel: 3 })
const educationOptions = ['专科', '本科', '硕士', '博士', 'Bachelor']

const averageScore = computed(() => {
  if (!recommendations.value.length) return 0
  return Math.round(recommendations.value.reduce((sum, item) => sum + item.totalScore, 0) / recommendations.value.length)
})
const profileCompletion = computed(() => {
  const fields = [profile.name, profile.college, profile.major, profile.education, preference.expectedJob, preference.expectedCity]
  const filled = fields.filter((value) => String(value || '').trim()).length
  return Math.round((filled + Math.min(skills.value.length, 3)) / 9 * 100)
})

const dimensions = [
  { key: 'skillScore', label: '技能', max: 40, color: '#43826f' },
  { key: 'experienceScore', label: '经历', max: 20, color: '#eb7954' },
  { key: 'directionScore', label: '方向', max: 15, color: '#6b638d' },
  { key: 'educationScore', label: '学历', max: 10, color: '#2f7094' },
  { key: 'cityScore', label: '城市', max: 10, color: '#89a842' },
  { key: 'salaryScore', label: '薪资', max: 5, color: '#c7903d' },
]

watch(() => props.initialTab, (value) => {
  activeTab.value = value
})

function showNotice(message) {
  notice.value = message
  window.clearTimeout(showNotice.timer)
  showNotice.timer = window.setTimeout(() => { notice.value = '' }, 2600)
}

function applyProfile(payload) {
  Object.assign(profile, payload.profile || {})
  Object.assign(preference, {
    expectedJob: '', expectedCity: '', expectedIndustry: '', salaryMin: 0, salaryMax: 0,
    acceptRemoteCity: true, ...(payload.preference || {}),
  })
  skills.value = payload.skills || []
}

async function loadProfile() {
  const payload = await apiRequest(props.apiBase, `/students/${props.studentId}/profile`)
  applyProfile(payload)
}

async function loadRecommendations() {
  const [items, gap] = await Promise.all([
    apiRequest(props.apiBase, `/recommendations/top10?studentId=${props.studentId}`),
    apiRequest(props.apiBase, `/recommendations/skill-gap?studentId=${props.studentId}`),
  ])
  recommendations.value = items
  skillGap.value = gap
}

async function loadWorkspace() {
  loading.value = true
  error.value = ''
  try {
    await Promise.all([loadProfile(), loadRecommendations()])
  } catch (cause) {
    error.value = cause.message
  } finally {
    loading.value = false
  }
}

async function saveProfile() {
  saving.value = 'profile'
  error.value = ''
  try {
    await apiRequest(props.apiBase, `/students/${props.studentId}/profile`, {
      method: 'PUT', body: JSON.stringify(profile),
    })
    showNotice('个人信息已保存')
  } catch (cause) {
    error.value = cause.message
  } finally {
    saving.value = ''
  }
}

async function savePreference() {
  saving.value = 'preference'
  error.value = ''
  try {
    await apiRequest(props.apiBase, `/students/${props.studentId}/preference`, {
      method: 'PUT', body: JSON.stringify({
        ...preference,
        salaryMin: Number(preference.salaryMin) || null,
        salaryMax: Number(preference.salaryMax) || null,
      }),
    })
    await loadRecommendations()
    showNotice('就业期望已保存，推荐结果已更新')
  } catch (cause) {
    error.value = cause.message
  } finally {
    saving.value = ''
  }
}

async function addSkill() {
  if (!newSkill.skillName.trim()) return
  saving.value = 'skill'
  error.value = ''
  try {
    await apiRequest(props.apiBase, `/students/${props.studentId}/skills`, {
      method: 'POST', body: JSON.stringify({
        skillName: newSkill.skillName.trim(), skillLevel: Number(newSkill.skillLevel),
      }),
    })
    newSkill.skillName = ''
    newSkill.skillLevel = 3
    await Promise.all([loadProfile(), loadRecommendations()])
    showNotice('技能已加入画像')
  } catch (cause) {
    error.value = cause.message
  } finally {
    saving.value = ''
  }
}

async function removeSkill(skill) {
  saving.value = `skill-${skill.id}`
  error.value = ''
  try {
    await apiRequest(props.apiBase, `/students/${props.studentId}/skills/${skill.id}`, { method: 'DELETE' })
    await Promise.all([loadProfile(), loadRecommendations()])
    showNotice(`已移除 ${skill.skillName}`)
  } catch (cause) {
    error.value = cause.message
  } finally {
    saving.value = ''
  }
}

async function refreshRecommendations() {
  saving.value = 'recommendations'
  error.value = ''
  try {
    await loadRecommendations()
    showNotice('推荐结果已刷新')
  } catch (cause) {
    error.value = cause.message
  } finally {
    saving.value = ''
  }
}

function salary(job) {
  if (!job.salaryMin || !job.salaryMax) return '薪资面议'
  return `${Math.round(job.salaryMin / 1000)}K-${Math.round(job.salaryMax / 1000)}K/月`
}

function scoreWidth(item, dimension) {
  return `${Math.min(100, Math.round((item[dimension.key] || 0) / dimension.max * 100))}%`
}

function toggleJob(jobKey) {
  expandedJob.value = expandedJob.value === jobKey ? '' : jobKey
}

onMounted(loadWorkspace)
</script>

<template>
  <section class="student-workspace">
    <div class="workspace-banner">
      <button class="icon-command back-command" type="button" title="返回岗位市场" @click="emit('back-to-market')">
        <ArrowLeft :size="18" />
      </button>
      <div class="workspace-title">
        <p class="eyebrow">学生就业工作台 · DEMO001</p>
        <h1>{{ profile.name || '学生画像' }}，把目标变成下一步行动。</h1>
        <p>画像由学生自主维护，推荐基于近期公开岗位计算，不代表录用结果。</p>
      </div>
      <div class="workspace-metrics" aria-label="画像与推荐摘要">
        <div><strong>{{ profileCompletion }}%</strong><span>画像完整度</span></div>
        <div><strong>{{ averageScore }}</strong><span>Top10 平均分</span></div>
        <div><strong>{{ skills.length }}</strong><span>已登记技能</span></div>
      </div>
    </div>

    <div class="workspace-tabs" role="tablist" aria-label="学生工作台视图">
      <button :class="{ active: activeTab === 'profile' }" role="tab" :aria-selected="activeTab === 'profile'" @click="activeTab = 'profile'">
        <UserRound :size="17" />画像与期望
      </button>
      <button :class="{ active: activeTab === 'recommendations' }" role="tab" :aria-selected="activeTab === 'recommendations'" @click="activeTab = 'recommendations'">
        <Sparkles :size="17" />Top10 推荐<span class="tab-count">{{ recommendations.length }}</span>
      </button>
    </div>

    <div v-if="notice" class="toast" role="status"><Check :size="16" />{{ notice }}</div>
    <div v-if="error" class="workspace-error" role="alert"><CircleAlert :size="17" /><span>{{ error }}</span><button type="button" title="关闭错误" @click="error = ''"><X :size="16" /></button></div>

    <div v-if="loading" class="workspace-loading"><LoaderCircle :size="28" /><span>正在读取学生画像与推荐结果</span></div>

    <div v-else-if="activeTab === 'profile'" class="profile-layout">
      <form class="editor-section" @submit.prevent="saveProfile">
        <div class="editor-heading">
          <div><span>01</span><h2>个人信息</h2></div>
          <button class="command primary" type="submit" :disabled="saving === 'profile'">
            <LoaderCircle v-if="saving === 'profile'" class="spin" :size="16" /><Save v-else :size="16" />保存信息
          </button>
        </div>
        <div class="form-grid">
          <label><span>姓名</span><input v-model="profile.name" required placeholder="填写姓名" /></label>
          <label><span>学号</span><input v-model="profile.studentNo" placeholder="填写学号" /></label>
          <label><span>学院</span><input v-model="profile.college" required placeholder="例如：计算机学院" /></label>
          <label><span>专业</span><input v-model="profile.major" required placeholder="例如：数据科学" /></label>
          <label><span>学历</span><SearchSelect v-model="profile.education" label="学历" placeholder="搜索学历" empty-label="清除学历" :options="educationOptions" /></label>
          <label><span>毕业年份</span><input v-model.number="profile.graduationYear" required type="number" min="2024" max="2100" /></label>
        </div>
      </form>

      <section class="editor-section skills-editor">
        <div class="editor-heading"><div><span>02</span><h2>技能清单</h2></div><small>等级 1-5</small></div>
        <form class="skill-add" @submit.prevent="addSkill">
          <input v-model="newSkill.skillName" aria-label="技能名称" placeholder="输入技能，例如 Hive" />
          <label><span>{{ newSkill.skillLevel }}</span><input v-model.number="newSkill.skillLevel" aria-label="技能等级" type="range" min="1" max="5" /></label>
          <button class="icon-command add-skill" type="submit" title="添加技能" :disabled="saving === 'skill' || !newSkill.skillName.trim()"><Plus :size="18" /></button>
        </form>
        <div v-if="skills.length" class="skill-list">
          <div v-for="skill in skills" :key="skill.id" class="skill-row">
            <div><strong>{{ skill.skillName }}</strong><span>LEVEL {{ skill.skillLevel }}</span></div>
            <div class="level-dots" :aria-label="`技能等级 ${skill.skillLevel}`"><i v-for="level in 5" :key="level" :class="{ filled: level <= skill.skillLevel }"></i></div>
            <button class="icon-command danger" type="button" :title="`移除 ${skill.skillName}`" :disabled="saving === `skill-${skill.id}`" @click="removeSkill(skill)"><Trash2 :size="16" /></button>
          </div>
        </div>
        <div v-else class="inline-empty"><BookOpenCheck :size="22" /><span>添加技能后才能计算岗位能力覆盖。</span></div>
      </section>

      <form class="editor-section preference-editor" @submit.prevent="savePreference">
        <div class="editor-heading">
          <div><span>03</span><h2>就业期望</h2></div>
          <button class="command primary" type="submit" :disabled="saving === 'preference'">
            <LoaderCircle v-if="saving === 'preference'" class="spin" :size="16" /><Target v-else :size="16" />保存并重算
          </button>
        </div>
        <div class="form-grid preference-grid">
          <label><span>岗位方向</span><SearchSelect v-model="preference.expectedJob" label="岗位方向" placeholder="搜索岗位方向" empty-label="不限方向" :options="categoryOptions" /></label>
          <label><span>期望城市</span><SearchSelect v-model="preference.expectedCity" label="期望城市" placeholder="搜索期望城市" empty-label="不限城市" :options="cityOptions" /></label>
          <label><span>期望行业</span><input v-model="preference.expectedIndustry" placeholder="可选" /></label>
          <label><span>最低月薪</span><input v-model.number="preference.salaryMin" type="number" min="0" step="1000" /></label>
          <label><span>最高月薪</span><input v-model.number="preference.salaryMax" type="number" min="0" step="1000" /></label>
          <label class="switch-field"><input v-model="preference.acceptRemoteCity" type="checkbox" /><span class="switch-track"><i></i></span><b>接受其他城市机会</b></label>
        </div>
      </form>
    </div>

    <div v-else class="recommendation-layout">
      <aside class="gap-rail">
        <div class="gap-heading"><Lightbulb :size="21" /><span>能力差距</span></div>
        <p>{{ skillGap?.suggestion || '完善技能后生成提升建议。' }}</p>
        <div class="gap-group"><span>已掌握</span><div><b v-for="skill in skillGap?.masteredSkills" :key="skill" class="mastered">{{ skill }}</b></div></div>
        <div class="gap-group"><span>优先补齐</span><div><b v-for="skill in skillGap?.missingSkills" :key="skill" class="missing">{{ skill }}</b></div></div>
        <button class="command secondary" type="button" @click="activeTab = 'profile'"><Plus :size="16" />更新技能画像</button>
      </aside>

      <section class="recommendation-results">
        <div class="recommendation-head">
          <div><p class="eyebrow">实时匹配 · 六维评分</p><h2>与你更接近的岗位</h2></div>
          <button class="icon-command refresh-command" type="button" title="刷新推荐" :disabled="saving === 'recommendations'" @click="refreshRecommendations"><RefreshCw :class="{ spin: saving === 'recommendations' }" :size="18" /></button>
        </div>

        <div v-if="!recommendations.length" class="recommendation-empty"><BriefcaseBusiness :size="28" /><h3>还没有推荐结果</h3><p>先完善岗位方向和技能画像，再重新计算。</p><button class="command primary" @click="activeTab = 'profile'">完善画像<ArrowRight :size="16" /></button></div>

        <article v-for="(item, index) in recommendations" v-else :key="item.job.jobKey" class="recommendation-row" :class="{ expanded: expandedJob === item.job.jobKey }">
          <button class="recommendation-summary" type="button" :aria-expanded="expandedJob === item.job.jobKey" @click="toggleJob(item.job.jobKey)">
            <span class="rank">{{ String(index + 1).padStart(2, '0') }}</span>
            <span class="score"><strong>{{ item.totalScore }}</strong><small>/ 100</small></span>
            <span class="job-main"><strong>{{ item.job.jobName }}</strong><small>{{ item.job.companyName }}</small></span>
            <span class="job-meta"><b><MapPin :size="13" />{{ item.job.city }}</b><b><WalletCards :size="13" />{{ salary(item.job) }}</b><b><GraduationCap :size="13" />{{ item.job.educationRequirement || '学历不限' }}</b></span>
            <ChevronDown class="row-chevron" :size="18" />
          </button>
          <div class="score-track" aria-label="匹配维度分数">
            <div v-for="dimension in dimensions" :key="dimension.key">
              <span>{{ dimension.label }}</span>
              <i><b :style="{ width: scoreWidth(item, dimension), background: dimension.color }"></b></i>
              <em>{{ item[dimension.key] }}/{{ dimension.max }}</em>
            </div>
          </div>
          <div v-if="expandedJob === item.job.jobKey" class="recommendation-detail">
            <div><span>推荐依据</span><p>{{ item.recommendationReason }}</p></div>
            <div><span>已匹配技能</span><p class="token-line"><b v-for="skill in item.matchedSkills" :key="skill" class="mastered">{{ skill }}</b><i v-if="!item.matchedSkills.length">暂无明确命中</i></p></div>
            <div><span>待补技能</span><p class="token-line"><b v-for="skill in item.missingSkills" :key="skill" class="missing">{{ skill }}</b><i v-if="!item.missingSkills.length">当前抽取技能已覆盖</i></p></div>
            <a class="command secondary" :href="item.job.jobUrl" target="_blank" rel="noreferrer">查看原始岗位<ExternalLink :size="15" /></a>
          </div>
        </article>
      </section>
    </div>
  </section>
</template>
