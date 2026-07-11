<script setup>
import { ArrowRight, Building2, ChartNoAxesCombined, GraduationCap, Sparkles, UserRound } from '@lucide/vue'

defineProps({
  jobCount: { type: String, default: '11,559' },
})

const emit = defineEmits(['select-student', 'select-university'])
</script>

<template>
  <section class="role-landing" aria-labelledby="role-landing-title">
    <header class="role-landing-header">
      <span class="brand-mark" aria-hidden="true"><i></i><i></i><i></i></span>
      <span>就业雷达</span>
      <small>高校智慧就业数据平台</small>
    </header>

    <div class="role-landing-body">
      <div class="role-landing-intro">
        <p class="eyebrow">请选择工作入口</p>
        <h1 id="role-landing-title">从你的视角<br />进入就业现场。</h1>
        <p>学生关注个人机会，高校关注人才培养与市场需求。选择身份后进入对应工作台。</p>
      </div>

      <div class="role-cards" aria-label="工作台身份选择">
        <button class="role-card student-role" type="button" aria-label="进入学生端" @click="emit('select-student')">
          <span class="role-card-icon"><UserRound :size="25" /></span>
          <span class="role-card-copy">
            <span class="role-card-label">学生端</span>
            <strong>我的求职工作台</strong>
            <small>岗位市场 · 个人画像 · 智能推荐</small>
          </span>
          <ArrowRight class="role-card-arrow" :size="20" aria-hidden="true" />
        </button>

        <button class="role-card university-role" type="button" aria-label="进入高校端" @click="emit('select-university')">
          <span class="role-card-icon"><Building2 :size="25" /></span>
          <span class="role-card-copy">
            <span class="role-card-label">高校端</span>
            <strong>培养需求分析工作台</strong>
            <small>岗位需求 · 技能组合 · 地区矩阵</small>
          </span>
          <ArrowRight class="role-card-arrow" :size="20" aria-hidden="true" />
        </button>
      </div>
    </div>

    <footer class="role-landing-evidence" aria-label="当前数据概览">
      <div><Sparkles :size="17" /><span>近期公开岗位</span><strong>{{ jobCount }}</strong></div>
      <div><ChartNoAxesCombined :size="17" /><span>Spark 处理链路</span><strong>已就绪</strong></div>
      <div><GraduationCap :size="17" /><span>数据分析范围</span><strong>市场需求</strong></div>
    </footer>
  </section>
</template>
