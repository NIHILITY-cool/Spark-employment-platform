<script setup>
import { computed, reactive, ref } from 'vue'
import { ArrowLeft, ArrowRight, Building2, Eye, EyeOff, GraduationCap } from '@lucide/vue'
import { apiRequest } from '../api/client'

const props = defineProps({ apiBase: { type: String, required: true }, role: { type: String, required: true } })
const emit = defineEmits(['authenticated', 'back'])

const mode = ref('login')
const loading = ref(false)
const error = ref('')
const showPassword = ref(false)
const form = reactive({ studentNo: '', name: '', username: '', password: '' })
const isStudent = computed(() => props.role === 'STUDENT')
const isRegister = computed(() => isStudent.value && mode.value === 'register')

function switchMode(next) {
  mode.value = next
  error.value = ''
}

async function submit() {
  loading.value = true
  error.value = ''
  try {
    const payload = isRegister.value
      ? await apiRequest(props.apiBase, '/auth/student/register', {
        method: 'POST', body: JSON.stringify({ studentNo: form.studentNo.trim(), name: form.name.trim(), password: form.password }),
      })
      : await apiRequest(props.apiBase, '/auth/login', {
        method: 'POST', body: JSON.stringify({ role: props.role, username: isStudent.value ? form.studentNo.trim() : form.username.trim(), password: form.password }),
      })
    emit('authenticated', payload)
  } catch (cause) {
    error.value = cause.message || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="auth-gateway">
    <header class="auth-brandbar">
      <span class="brand-mark" aria-hidden="true"><i></i><i></i><i></i></span>
      <strong>就业雷达</strong>
      <button type="button" @click="emit('back')"><ArrowLeft :size="16" />返回入口</button>
    </header>

    <div class="auth-stage">
      <div class="auth-context" :class="isStudent ? 'student-auth-context' : 'university-auth-context'">
        <span class="auth-role-icon"><GraduationCap v-if="isStudent" :size="30" /><Building2 v-else :size="30" /></span>
        <p class="eyebrow">{{ isStudent ? '学生登录' : '高校登录' }}</p>
        <h1>{{ isStudent ? '继续完善你的求职准备' : '查看学生就业准备情况' }}</h1>
        <p>{{ isStudent ? '维护个人画像与求职期望，查看岗位推荐和能力差距。' : '查看岗位市场、学生匹配情况和需要重点支持的学生。' }}</p>
      </div>

      <form class="auth-form" @submit.prevent="submit">
        <div class="auth-form-head">
          <div><p class="eyebrow">{{ isRegister ? '创建学生账号' : '登录工作台' }}</p><h2>{{ isRegister ? '使用学号注册' : (isStudent ? '学生登录' : '高校登录') }}</h2></div>
          <div v-if="isStudent" class="auth-mode-switch" role="tablist" aria-label="登录注册切换">
            <button type="button" role="tab" :class="{ active: mode === 'login' }" @click="switchMode('login')">登录</button>
            <button type="button" role="tab" :class="{ active: mode === 'register' }" @click="switchMode('register')">注册</button>
          </div>
        </div>

        <label v-if="isStudent"><span>学号</span><input v-model="form.studentNo" autocomplete="username" maxlength="64" required placeholder="请输入学号" /></label>
        <label v-else><span>高校账号</span><input v-model="form.username" autocomplete="username" maxlength="64" required placeholder="请输入高校统一账号" /></label>
        <label v-if="isRegister"><span>姓名</span><input v-model="form.name" autocomplete="name" maxlength="64" required placeholder="请输入真实姓名" /></label>
        <label><span>密码</span><span class="password-field"><input v-model="form.password" :type="showPassword ? 'text' : 'password'" autocomplete="current-password" :minlength="isRegister ? 6 : undefined" maxlength="72" required :placeholder="isRegister ? '至少 6 位' : '请输入密码'" /><button type="button" :title="showPassword ? '隐藏密码' : '显示密码'" @click="showPassword = !showPassword"><EyeOff v-if="showPassword" :size="17" /><Eye v-else :size="17" /></button></span></label>

        <p v-if="error" class="auth-error">{{ error }}</p>
        <button class="auth-submit" type="submit" :disabled="loading"><span>{{ loading ? '正在验证…' : (isRegister ? '注册并进入' : '进入工作台') }}</span><ArrowRight :size="17" /></button>
      </form>
    </div>
  </section>
</template>
