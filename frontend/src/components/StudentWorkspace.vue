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
  LoaderCircle,
  MapPin,
  Pencil,
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
import DatePicker from './DatePicker.vue'
import SearchSelect from './SearchSelect.vue'

const props = defineProps({
  apiBase: { type: String, required: true },
  studentId: { type: Number, default: 1 },
  cityOptions: { type: Array, default: () => [] },
  categoryOptions: { type: Array, default: () => [] },
  initialTab: { type: String, default: 'profile' },
})

const emit = defineEmits(['back-to-market', 'tab-change'])

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
const skillPage = ref(1)
const experiences = ref([])
const recommendations = ref([])
const newSkill = reactive({ skillName: '', skillLevel: 3 })
const experienceDraft = reactive({
  id: null, experienceType: 'project', title: '', organization: '', role: '',
  description: '', startDate: '', endDate: '',
})
const educationOptions = ['专科', '本科', '硕士', '博士', 'Bachelor']
const SKILLS_PER_PAGE = 7
const experienceTypes = [
  { value: 'project', label: '项目经历' },
  { value: 'internship', label: '实习经历' },
  { value: 'award', label: '获奖经历' },
]

const averageScore = computed(() => {
  if (!recommendations.value.length) return 0
  return Math.round(recommendations.value.reduce((sum, item) => sum + item.totalScore, 0) / recommendations.value.length)
})
const profileCompletion = computed(() => {
  const fields = [profile.name, profile.college, profile.major, profile.education, preference.expectedJob, preference.expectedCity]
  const filled = fields.filter((value) => String(value || '').trim()).length
  return Math.round((filled + Math.min(experiences.value.length, 2) + Math.min(skills.value.length, 2)) / 10 * 100)
})
const skillPageCount = computed(() => Math.max(1, Math.ceil(skills.value.length / SKILLS_PER_PAGE)))
const visibleSkills = computed(() => skills.value.slice((skillPage.value - 1) * SKILLS_PER_PAGE, skillPage.value * SKILLS_PER_PAGE))
const topExperienceTerms = computed(() => [...new Set(recommendations.value.flatMap((item) => item.matchedExperienceTerms || []))].slice(0, 6))

const dimensions = [
  { key: 'experienceScore', label: '经历', max: 40, color: '#eb7954' },
  { key: 'directionScore', label: '方向', max: 30, color: '#6b638d' },
  { key: 'cityScore', label: '城市', max: 10, color: '#89a842' },
  { key: 'industryScore', label: '行业', max: 5, color: '#9b6d8f' },
  { key: 'salaryScore', label: '薪资', max: 10, color: '#c7903d' },
  { key: 'freshnessScore', label: '时效', max: 5, color: '#557985' },
]

watch(() => props.initialTab, (value) => {
  activeTab.value = value
})

function selectTab(tab) {
  if (activeTab.value === tab) return
  activeTab.value = tab
  emit('tab-change', tab)
}

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
  if (skillPage.value > Math.max(1, Math.ceil(skills.value.length / SKILLS_PER_PAGE))) skillPage.value = 1
  experiences.value = payload.experiences || []
}

async function loadProfile() {
  const payload = await apiRequest(props.apiBase, `/students/${props.studentId}/profile`)
  applyProfile(payload)
}

async function loadRecommendations() {
  recommendations.value = await apiRequest(props.apiBase, `/recommendations/top10?studentId=${props.studentId}`)
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

async function saveIdentity() {
  saving.value = 'identity'
  error.value = ''
  try {
    await Promise.all([
      apiRequest(props.apiBase, `/students/${props.studentId}/profile`, {
        method: 'PUT', body: JSON.stringify(profile),
      }),
      apiRequest(props.apiBase, `/students/${props.studentId}/preference`, {
        method: 'PUT', body: JSON.stringify({
          ...preference,
          salaryMin: Number(preference.salaryMin) || null,
          salaryMax: null,
        }),
      }),
    ])
    await loadRecommendations()
    showNotice('个人画像已保存，推荐结果已更新')
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

function experienceTypeLabel(type) {
  return experienceTypes.find((item) => item.value === type)?.label || '实践经历'
}

function resetExperienceDraft() {
  Object.assign(experienceDraft, {
    id: null, experienceType: 'project', title: '', organization: '', role: '',
    description: '', startDate: '', endDate: '',
  })
}

function editExperience(experience) {
  Object.assign(experienceDraft, {
    id: experience.id,
    experienceType: experience.experienceType,
    title: experience.title || '',
    organization: experience.organization || '',
    role: experience.role || '',
    description: experience.description || '',
    startDate: experience.startDate || '',
    endDate: experience.endDate || '',
  })
  document.querySelector('.experience-form')?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

async function saveExperience() {
  if (!experienceDraft.title.trim() || !experienceDraft.description.trim()) return
  saving.value = 'experience'
  error.value = ''
  try {
    const path = experienceDraft.id
      ? `/students/${props.studentId}/experiences/${experienceDraft.id}`
      : `/students/${props.studentId}/experiences`
    await apiRequest(props.apiBase, path, {
      method: experienceDraft.id ? 'PUT' : 'POST',
      body: JSON.stringify({
        ...experienceDraft,
        id: undefined,
        startDate: experienceDraft.startDate || null,
        endDate: experienceDraft.endDate || null,
      }),
    })
    const message = experienceDraft.id ? '经历已更新，推荐结果已重算' : '经历已加入画像，推荐结果已重算'
    resetExperienceDraft()
    await Promise.all([loadProfile(), loadRecommendations()])
    showNotice(message)
  } catch (cause) {
    error.value = cause.message
  } finally {
    saving.value = ''
  }
}

async function removeExperience(experience) {
  saving.value = `experience-${experience.id}`
  error.value = ''
  try {
    await apiRequest(props.apiBase, `/students/${props.studentId}/experiences/${experience.id}`, { method: 'DELETE' })
    if (experienceDraft.id === experience.id) resetExperienceDraft()
    await Promise.all([loadProfile(), loadRecommendations()])
    showNotice('经历已移除，推荐结果已重算')
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
        <p class="eyebrow">学生就业工作台</p>
        <h1>{{ profile.name || '学生画像' }}，把目标变成下一步行动。</h1>
      </div>
      <div class="workspace-metrics" aria-label="画像与推荐摘要">
        <div><strong>{{ profileCompletion }}%</strong><span>画像完整度</span></div>
        <div><strong>{{ averageScore }}</strong><span>Top10 平均分</span></div>
        <div><strong>{{ experiences.length }}</strong><span>实践证据</span></div>
      </div>
    </div>

    <div class="workspace-tabs" role="tablist" aria-label="学生工作台视图">
      <button :class="{ active: activeTab === 'profile' }" role="tab" :aria-selected="activeTab === 'profile'" @click="selectTab('profile')">
        <UserRound :size="17" />画像与期望
      </button>
      <button :class="{ active: activeTab === 'recommendations' }" role="tab" :aria-selected="activeTab === 'recommendations'" @click="selectTab('recommendations')">
        <Sparkles :size="17" />Top10 推荐<span class="tab-count">{{ recommendations.length }}</span>
      </button>
    </div>

    <div v-if="notice" class="toast" role="status"><Check :size="16" />{{ notice }}</div>
    <div v-if="error" class="workspace-error" role="alert"><CircleAlert :size="17" /><span>{{ error }}</span><button type="button" title="关闭错误" @click="error = ''"><X :size="16" /></button></div>

    <div v-if="loading" class="workspace-loading"><LoaderCircle :size="28" /><span>正在读取学生画像与推荐结果</span></div>

    <div v-else-if="activeTab === 'profile'" class="profile-layout">
      <form class="editor-section identity-editor" @submit.prevent="saveIdentity">
        <div class="editor-heading">
          <div><span>01</span><h2>个人信息</h2></div>
          <button class="command primary" type="submit" :disabled="saving === 'identity'">
            <LoaderCircle v-if="saving === 'identity'" class="spin" :size="16" /><Save v-else :size="16" />保存并重算
          </button>
        </div>
        <p class="identity-group-title">基本资料</p>
        <div class="form-grid">
          <label><span>姓名</span><input v-model="profile.name" required placeholder="填写姓名" /></label>
          <label><span>学号</span><input v-model="profile.studentNo" placeholder="填写学号" /></label>
          <label><span>学院</span><input v-model="profile.college" required placeholder="例如：计算机学院" /></label>
          <label><span>专业</span><input v-model="profile.major" required placeholder="例如：数据科学" /></label>
          <label><span>学历</span><SearchSelect v-model="profile.education" label="学历" placeholder="搜索学历" empty-label="清除学历" :options="educationOptions" /></label>
          <label><span>毕业年份</span><input v-model.number="profile.graduationYear" required type="number" min="2024" max="2100" /></label>
        </div>
        <p class="identity-group-title">就业期望</p>
        <div class="form-grid">
          <label><span>岗位方向</span><SearchSelect v-model="preference.expectedJob" label="岗位方向" placeholder="搜索岗位方向" empty-label="不限方向" :options="categoryOptions" /></label>
          <label><span>期望城市</span><SearchSelect v-model="preference.expectedCity" label="期望城市" placeholder="搜索期望城市" empty-label="不限城市" :options="cityOptions" /></label>
          <label><span>期望行业</span><input v-model="preference.expectedIndustry" placeholder="可选" /></label>
          <label><span>期望最低月薪</span><input v-model.number="preference.salaryMin" type="number" min="0" step="1000" placeholder="例如 8000" /></label>
          <label class="switch-field"><input v-model="preference.acceptRemoteCity" type="checkbox" /><span class="switch-track"><i></i></span><b>接受其他城市机会</b></label>
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
          <div v-for="skill in visibleSkills" :key="skill.id" class="skill-row">
            <div><strong>{{ skill.skillName }}</strong><span>LEVEL {{ skill.skillLevel }}</span></div>
            <div class="level-dots" :aria-label="`技能等级 ${skill.skillLevel}`"><i v-for="level in 5" :key="level" :class="{ filled: level <= skill.skillLevel }"></i></div>
            <button class="icon-command danger" type="button" :title="`移除 ${skill.skillName}`" :disabled="saving === `skill-${skill.id}`" @click="removeSkill(skill)"><Trash2 :size="16" /></button>
          </div>
          <div v-if="skillPageCount > 1" class="skill-pagination">
            <button class="icon-command" type="button" title="上一页技能" :disabled="skillPage === 1" @click="skillPage--"><ArrowLeft :size="15" /></button>
            <span>第 {{ skillPage }} / {{ skillPageCount }} 页</span>
            <button class="icon-command" type="button" title="下一页技能" :disabled="skillPage === skillPageCount" @click="skillPage++"><ArrowRight :size="15" /></button>
          </div>
        </div>
        <div v-else class="inline-empty"><BookOpenCheck :size="22" /><span>暂未登记个人技能。</span></div>
      </section>

      <section class="editor-section evidence-editor">
        <div class="editor-heading">
          <div><span>03</span><h2>实践与成果</h2></div>
          <small>经历相关性占匹配分 40%</small>
        </div>
        <form class="experience-form" @submit.prevent="saveExperience">
          <div class="experience-type-control" aria-label="经历类型">
            <button v-for="type in experienceTypes" :key="type.value" type="button" :class="{ active: experienceDraft.experienceType === type.value }" :aria-pressed="experienceDraft.experienceType === type.value" @click="experienceDraft.experienceType = type.value">{{ type.label }}</button>
          </div>
          <div class="experience-fields">
            <label><span>名称</span><input v-model="experienceDraft.title" required :placeholder="experienceDraft.experienceType === 'award' ? '例如：全国大学生数据竞赛一等奖' : '例如：校园就业数据分析平台'" /></label>
            <label><span>{{ experienceDraft.experienceType === 'award' ? '颁发单位' : '组织 / 单位' }}</span><input v-model="experienceDraft.organization" placeholder="学校、实验室或企业" /></label>
            <label><span>{{ experienceDraft.experienceType === 'award' ? '奖项级别' : '承担角色' }}</span><input v-model="experienceDraft.role" :placeholder="experienceDraft.experienceType === 'award' ? '国家级 / 省级 / 校级' : '负责人 / 后端开发 / 数据分析'" /></label>
            <label class="experience-date"><span>开始时间</span><DatePicker v-model="experienceDraft.startDate" label="开始时间" /></label>
            <label class="experience-date"><span>结束时间</span><DatePicker v-model="experienceDraft.endDate" label="结束时间" /></label>
            <label class="experience-description"><span>职责与成果</span><textarea v-model="experienceDraft.description" rows="3" required placeholder="写清做了什么、使用了什么方法，以及可验证的结果，例如：负责 SQL 数据分析，上线后报表效率提升 30%"></textarea></label>
          </div>
          <div class="experience-actions">
            <button v-if="experienceDraft.id" class="command secondary" type="button" @click="resetExperienceDraft"><X :size="15" />取消编辑</button>
            <button class="command primary" type="submit" :disabled="saving === 'experience' || !experienceDraft.title.trim() || !experienceDraft.description.trim()">
              <LoaderCircle v-if="saving === 'experience'" class="spin" :size="16" /><Save v-else-if="experienceDraft.id" :size="16" /><Plus v-else :size="16" />{{ experienceDraft.id ? '保存修改' : '添加经历' }}
            </button>
          </div>
        </form>
        <div v-if="experiences.length" class="experience-list">
          <article v-for="experience in experiences" :key="experience.id" class="experience-row">
            <span class="experience-kind">{{ experienceTypeLabel(experience.experienceType) }}</span>
            <div><strong>{{ experience.title }}</strong><small>{{ [experience.organization, experience.role].filter(Boolean).join(' · ') || '学生自主填写' }}</small><p>{{ experience.description }}</p></div>
            <time>{{ experience.startDate || '未填时间' }}<template v-if="experience.endDate"> — {{ experience.endDate }}</template></time>
            <div class="experience-row-actions">
              <button class="icon-command" type="button" :title="`编辑 ${experience.title}`" @click="editExperience(experience)"><Pencil :size="15" /></button>
              <button class="icon-command danger" type="button" :title="`删除 ${experience.title}`" :disabled="saving === `experience-${experience.id}`" @click="removeExperience(experience)"><Trash2 :size="15" /></button>
            </div>
          </article>
        </div>
        <div v-else class="inline-empty"><BriefcaseBusiness :size="22" /><span>添加项目、实习或获奖经历后，推荐会优先匹配岗位职责相关证据。</span></div>
      </section>

    </div>

    <div v-else class="recommendation-layout">
      <aside class="match-overview">
        <div class="match-overview-head"><Target :size="19" /><span>匹配概况</span></div>
        <dl>
          <div><dt>求职方向</dt><dd>{{ preference.expectedJob || '不限方向' }}</dd></div>
          <div><dt>最低月薪</dt><dd>{{ preference.salaryMin ? `${Math.round(preference.salaryMin / 1000)}K` : '未设置' }}</dd></div>
          <div><dt>实践证据</dt><dd>{{ experiences.length }} 条</dd></div>
        </dl>
        <div class="overview-terms"><span>经历命中</span><div><b v-for="term in topExperienceTerms" :key="term">{{ term }}</b><i v-if="!topExperienceTerms.length">暂无</i></div></div>
        <button class="command secondary" type="button" @click="selectTab('profile')"><Plus :size="16" />更新完整画像</button>
      </aside>

      <section class="recommendation-results">
        <div class="recommendation-head">
          <div><p class="eyebrow">学历硬筛选 · 六维证据评分</p><h2>与你更接近的岗位</h2></div>
          <button class="icon-command refresh-command" type="button" title="刷新推荐" :disabled="saving === 'recommendations'" @click="refreshRecommendations"><RefreshCw :class="{ spin: saving === 'recommendations' }" :size="18" /></button>
        </div>

        <div v-if="!recommendations.length" class="recommendation-empty"><BriefcaseBusiness :size="28" /><h3>还没有推荐结果</h3><p>先完善岗位方向和实践经历，再重新计算。</p><button class="command primary" @click="selectTab('profile')">完善画像<ArrowRight :size="16" /></button></div>

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
            <div><span>经历命中</span><p class="token-line"><b v-for="term in item.matchedExperienceTerms" :key="term" class="experience-match">{{ term }}</b><i v-if="!item.matchedExperienceTerms.length">暂无职责相关经历词</i></p></div>
            <div><span>岗位门槛</span><p>{{ item.job.educationRequirement || '学历不限' }} · {{ item.job.experienceRequirement || '经验不限' }}</p></div>
            <a class="command secondary" :href="item.job.jobUrl" target="_blank" rel="noreferrer">查看原始岗位<ExternalLink :size="15" /></a>
          </div>
        </article>
      </section>
    </div>
  </section>
</template>
