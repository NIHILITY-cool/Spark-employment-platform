<script setup>
import { computed } from 'vue'
import { Building2, CalendarDays, ExternalLink, GraduationCap, MapPin, Wallet, X } from '@lucide/vue'

const props = defineProps({
  detail: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
})
const emit = defineEmits(['close'])

const job = computed(() => props.detail?.job || null)
const skills = computed(() => props.detail?.skills || [])

function salary(item) {
  if (!item?.salaryMin || !item?.salaryMax) return item?.salaryRaw || '薪资面议'
  return `${Math.round(item.salaryMin / 1000)}K-${Math.round(item.salaryMax / 1000)}K / 月`
}

function valueOrFallback(value, fallback = '未说明') {
  return value || fallback
}
</script>

<template>
  <Transition name="job-detail">
    <div v-if="job" class="job-detail-backdrop" @click.self="emit('close')">
      <aside class="job-detail-drawer" role="dialog" aria-modal="true" :aria-label="`${job.jobName}岗位详情`">
        <header class="job-detail-header">
          <div>
            <span class="category-tag">{{ job.jobCategory || '其他' }}</span>
            <h2>{{ job.jobName }}</h2>
            <p><Building2 :size="15" />{{ job.companyName }}</p>
          </div>
          <button class="job-detail-close" type="button" aria-label="关闭岗位详情" @click="emit('close')"><X :size="20" /></button>
        </header>

        <div class="job-detail-body">
          <section class="job-detail-overview" aria-label="岗位基础信息">
            <div><Wallet :size="17" /><span>薪资</span><strong>{{ salary(job) }}</strong></div>
            <div><MapPin :size="17" /><span>工作地点</span><strong>{{ valueOrFallback(job.city) }}{{ job.district ? ` · ${job.district}` : '' }}</strong></div>
            <div><GraduationCap :size="17" /><span>学历要求</span><strong>{{ valueOrFallback(job.educationRequirement) }}</strong></div>
            <div><CalendarDays :size="17" /><span>经验要求</span><strong>{{ valueOrFallback(job.experienceRequirement) }}</strong></div>
          </section>

          <section class="job-detail-section">
            <div class="job-detail-section-head"><h3>岗位描述</h3><span>{{ job.sourceName || '公开岗位来源' }}</span></div>
            <div v-if="loading" class="job-detail-skeleton" aria-label="正在加载岗位描述"><i></i><i></i><i></i><i></i></div>
            <p v-else class="job-description">{{ valueOrFallback(job.jobDescription, '该岗位暂未提供完整描述。') }}</p>
            <p v-if="error" class="job-detail-error">{{ error }}，当前展示的是岗位列表中的基础信息。</p>
          </section>

          <section class="job-detail-section">
            <div class="job-detail-section-head"><h3>岗位技能</h3><span>{{ skills.length }} 项提取结果</span></div>
            <div v-if="loading" class="job-skill-skeleton"><i v-for="item in 5" :key="item"></i></div>
            <div v-else-if="skills.length" class="job-skill-tags"><span v-for="skill in skills" :key="skill.skillName">{{ skill.skillName }}</span></div>
            <p v-else class="job-description muted">暂无可展示的技能提取结果。</p>
          </section>

          <section class="job-detail-footnote">
            <span>行业：{{ valueOrFallback(job.industry) }}</span>
            <span>公司规模：{{ valueOrFallback(job.companyScale) }}</span>
            <span>最近采集：{{ valueOrFallback(job.lastSeenDate || job.crawlDate) }}</span>
          </section>
        </div>

        <footer class="job-detail-actions">
          <span>岗位信息来自公开招聘数据</span>
          <a v-if="job.jobUrl" :href="job.jobUrl" target="_blank" rel="noopener noreferrer">打开原岗位链接 <ExternalLink :size="16" /></a>
        </footer>
      </aside>
    </div>
  </Transition>
</template>
