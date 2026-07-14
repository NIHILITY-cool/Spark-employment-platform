<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { Building2, KeyRound, LogOut, RefreshCw, ShieldCheck, UserRound } from '@lucide/vue'
import { apiRequest, clearAuthSession, getAuthSession, saveAuthSession } from '../api/client'

const props = defineProps({ apiBase: { type: String, required: true } })

const authenticated = ref(false)
const loading = ref(false)
const error = ref('')
const notice = ref('')
const accounts = ref([])
const login = reactive({ username: 'admin', password: '' })
const university = reactive({ username: 'university', password: '' })
const resetTarget = ref(null)
const resetPassword = ref('')
const students = computed(() => accounts.value.filter((item) => item.role === 'STUDENT'))
const universityAccount = computed(() => accounts.value.find((item) => item.role === 'UNIVERSITY'))

async function signIn() {
  loading.value = true
  error.value = ''
  try {
    const session = await apiRequest(props.apiBase, '/auth/login', {
      method: 'POST', body: JSON.stringify({ role: 'ADMIN', username: login.username, password: login.password }),
    })
    saveAuthSession(session)
    authenticated.value = true
    await loadAccounts()
  } catch (cause) {
    error.value = cause.message || '管理员登录失败'
  } finally {
    loading.value = false
  }
}

async function loadAccounts() {
  accounts.value = await apiRequest(props.apiBase, '/admin/accounts')
  university.username = universityAccount.value?.username || 'university'
}

async function saveUniversity() {
  await action('高校统一账号已更新，原有高校会话已退出', async () => {
    await apiRequest(props.apiBase, '/admin/university-credential', {
      method: 'PUT', body: JSON.stringify({ username: university.username, password: university.password }),
    })
    university.password = ''
    await loadAccounts()
  })
}

async function toggleAccount(account) {
  await action(account.enabled ? '账号已停用' : '账号已启用', async () => {
    await apiRequest(props.apiBase, `/admin/accounts/${account.id}/status`, {
      method: 'PUT', body: JSON.stringify({ enabled: !account.enabled }),
    })
    await loadAccounts()
  })
}

async function submitReset() {
  if (!resetTarget.value) return
  await action('密码已重置，原有会话已退出', async () => {
    await apiRequest(props.apiBase, `/admin/accounts/${resetTarget.value.id}/password`, {
      method: 'PUT', body: JSON.stringify({ password: resetPassword.value }),
    })
    resetTarget.value = null
    resetPassword.value = ''
  })
}

async function action(message, callback) {
  loading.value = true
  error.value = ''
  notice.value = ''
  try {
    await callback()
    notice.value = message
  } catch (cause) {
    error.value = cause.message || '操作失败'
  } finally {
    loading.value = false
  }
}

function signOut() {
  clearAuthSession()
  authenticated.value = false
  accounts.value = []
}

function formatTime(value) {
  return value ? new Date(value).toLocaleString('zh-CN', { hour12: false }) : '-'
}

onMounted(async () => {
  if (getAuthSession()?.account?.role !== 'ADMIN') return
  try {
    const me = await apiRequest(props.apiBase, '/auth/me')
    if (me.role === 'ADMIN') {
      authenticated.value = true
      await loadAccounts()
    }
  } catch {
    clearAuthSession()
  }
})
</script>

<template>
  <main class="admin-shell">
    <section v-if="!authenticated" class="admin-login">
      <div class="admin-login-mark"><ShieldCheck :size="34" /></div>
      <p class="eyebrow">管理员登录</p>
      <h1>账号管理</h1>
      <p>登录后管理学生账号和高校端账号。</p>
      <form @submit.prevent="signIn">
        <label><span>管理员账号</span><input v-model="login.username" autocomplete="username" required /></label>
        <label><span>管理员密码</span><input v-model="login.password" type="password" autocomplete="current-password" required /></label>
        <p v-if="error" class="admin-message error">{{ error }}</p>
        <button type="submit" :disabled="loading"><ShieldCheck :size="16" />{{ loading ? '正在验证…' : '进入管理端' }}</button>
      </form>
    </section>

    <template v-else>
      <header class="admin-topbar">
        <div><ShieldCheck :size="20" /><strong>就业雷达管理端</strong><span>/admin</span></div>
        <button type="button" title="退出管理端" @click="signOut"><LogOut :size="17" /></button>
      </header>

      <section class="admin-heading">
        <div><p class="eyebrow">账号管理</p><h1>学生与高校账号</h1></div>
        <div class="admin-counts"><span>学生账号 <strong>{{ students.length }}</strong></span><span>已启用 <strong>{{ students.filter((item) => item.enabled).length }}</strong></span></div>
      </section>

      <p v-if="notice" class="admin-message notice">{{ notice }}</p>
      <p v-if="error" class="admin-message error">{{ error }}</p>

      <section class="admin-grid">
        <div class="admin-account-panel">
          <div class="admin-section-head"><div><p class="eyebrow">学生账号</p><h2>注册学生</h2></div><button type="button" title="刷新账号" @click="loadAccounts"><RefreshCw :size="16" /></button></div>
          <div class="admin-account-table">
            <div class="admin-table-head"><span>学生</span><span>学号</span><span>更新时间</span><span>状态</span><span>操作</span></div>
            <div v-for="account in students" :key="account.id" class="admin-account-row">
              <span class="admin-person"><UserRound :size="15" /><b>{{ account.displayName }}</b></span>
              <span>{{ account.username }}</span><span>{{ formatTime(account.updatedAt) }}</span>
              <span :class="account.enabled ? 'enabled' : 'disabled'">{{ account.enabled ? '启用' : '停用' }}</span>
              <span class="admin-row-actions"><button type="button" title="重置密码" @click="resetTarget = account"><KeyRound :size="15" /></button><button type="button" @click="toggleAccount(account)">{{ account.enabled ? '停用' : '启用' }}</button></span>
            </div>
            <p v-if="!students.length" class="admin-empty">还没有学生注册。</p>
          </div>
        </div>

        <aside class="admin-university-panel">
          <div class="admin-section-head"><div><p class="eyebrow">高校统一身份</p><h2>高校端账号</h2></div><Building2 :size="20" /></div>
          <form @submit.prevent="saveUniversity">
            <label><span>账号</span><input v-model="university.username" required maxlength="64" /></label>
            <label><span>新密码</span><input v-model="university.password" type="password" required minlength="6" maxlength="72" placeholder="输入新密码" /></label>
            <button type="submit" :disabled="loading">更新高校账号</button>
          </form>
          <p>修改后，已登录的高校端需要重新登录。</p>
        </aside>
      </section>

      <div v-if="resetTarget" class="admin-dialog-backdrop" @click.self="resetTarget = null">
        <form class="admin-reset-dialog" role="dialog" aria-modal="true" :aria-label="`重置${resetTarget.displayName}的密码`" @submit.prevent="submitReset">
          <KeyRound :size="23" /><h2>重置学生密码</h2><p>{{ resetTarget.displayName }} · {{ resetTarget.username }}</p>
          <label><span>新密码</span><input v-model="resetPassword" type="password" required minlength="6" maxlength="72" autofocus /></label>
          <div><button type="button" @click="resetTarget = null">取消</button><button type="submit">确认重置</button></div>
        </form>
      </div>
    </template>
  </main>
</template>
