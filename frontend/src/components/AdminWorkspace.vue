<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import {
  Building2, ChevronLeft, ChevronRight, KeyRound, LogOut, RefreshCw,
  Search, ShieldCheck, UserCheck, UserRound, Users, UserX,
} from '@lucide/vue'
import { apiRequest, clearAuthSession, getAuthSession, saveAuthSession } from '../api/client'

const props = defineProps({ apiBase: { type: String, required: true } })
const PAGE_SIZE = 12

const authenticated = ref(false)
const loading = ref(false)
const error = ref('')
const notice = ref('')
const accounts = ref([])
const query = ref('')
const status = ref('all')
const page = ref(1)
const login = reactive({ username: 'admin', password: '' })
const university = reactive({ username: 'university', password: '' })
const resetTarget = ref(null)
const resetPassword = ref('')

const students = computed(() => accounts.value.filter((item) => item.role === 'STUDENT'))
const universityAccount = computed(() => accounts.value.find((item) => item.role === 'UNIVERSITY'))
const enabledCount = computed(() => students.value.filter((item) => item.enabled).length)
const disabledCount = computed(() => students.value.length - enabledCount.value)
const filteredStudents = computed(() => {
  const keyword = query.value.trim().toLowerCase()
  return students.value.filter((item) => {
    const matchesQuery = !keyword || `${item.displayName} ${item.username}`.toLowerCase().includes(keyword)
    const matchesStatus = status.value === 'all' || (status.value === 'enabled' ? item.enabled : !item.enabled)
    return matchesQuery && matchesStatus
  })
})
const pageCount = computed(() => Math.max(1, Math.ceil(filteredStudents.value.length / PAGE_SIZE)))
const visibleStudents = computed(() => {
  const start = (page.value - 1) * PAGE_SIZE
  return filteredStudents.value.slice(start, start + PAGE_SIZE)
})

watch([query, status], () => { page.value = 1 })
watch(pageCount, (count) => { if (page.value > count) page.value = count })

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

async function refreshAccounts() {
  await action('账号数据已刷新', loadAccounts)
}

async function saveUniversity() {
  await action('高校账号已更新，原有会话已退出', async () => {
    await apiRequest(props.apiBase, '/admin/university-credential', {
      method: 'PUT', body: JSON.stringify({ username: university.username, password: university.password }),
    })
    university.password = ''
    await loadAccounts()
  })
}

async function toggleAccount(account) {
  await action(account.enabled ? '学生账号已停用' : '学生账号已启用', async () => {
    await apiRequest(props.apiBase, `/admin/accounts/${account.id}/status`, {
      method: 'PUT', body: JSON.stringify({ enabled: !account.enabled }),
    })
    await loadAccounts()
  })
}

async function submitReset() {
  if (!resetTarget.value) return
  await action('学生密码已重置，原有会话已退出', async () => {
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

function openReset(account) {
  resetPassword.value = ''
  resetTarget.value = account
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
      <div class="admin-login-mark"><ShieldCheck :size="28" /></div>
      <div class="admin-login-copy">
        <span>平台维护入口</span>
        <h1>账号管理</h1>
        <p>仅管理员可查看和维护平台账号。</p>
      </div>
      <form @submit.prevent="signIn">
        <label><span>管理员账号</span><input v-model="login.username" autocomplete="username" required /></label>
        <label><span>管理员密码</span><input v-model="login.password" type="password" autocomplete="current-password" required /></label>
        <p v-if="error" class="admin-message error" role="alert">{{ error }}</p>
        <button class="admin-primary" type="submit" :disabled="loading">
          <ShieldCheck :size="16" />{{ loading ? '正在验证...' : '进入管理端' }}
        </button>
      </form>
    </section>

    <template v-else>
      <header class="admin-topbar">
        <div class="admin-brand"><ShieldCheck :size="19" /><strong>就业雷达</strong><span>管理端</span></div>
        <button class="admin-logout" type="button" @click="signOut"><LogOut :size="16" />退出</button>
      </header>

      <div class="admin-content">
        <section class="admin-heading">
          <div><p>账号与访问</p><h1>学生与高校账号</h1><span>查看学生账号状态，处理登录问题，维护高校统一账号。</span></div>
          <button type="button" :disabled="loading" @click="refreshAccounts"><RefreshCw :size="16" />刷新</button>
        </section>

        <section class="admin-metrics" aria-label="账号概况">
          <div><Users :size="19" /><span>学生账号</span><strong>{{ students.length }}</strong></div>
          <div><UserCheck :size="19" /><span>正常使用</span><strong>{{ enabledCount }}</strong></div>
          <div><UserX :size="19" /><span>已停用</span><strong>{{ disabledCount }}</strong></div>
        </section>

        <p v-if="notice" class="admin-message notice" role="status">{{ notice }}</p>
        <p v-if="error" class="admin-message error" role="alert">{{ error }}</p>

        <section class="admin-grid">
          <div class="admin-account-panel">
            <div class="admin-section-head">
              <div><h2>学生账号</h2><p>共 {{ filteredStudents.length }} 条符合当前条件</p></div>
              <div class="admin-tools">
                <label class="admin-search"><Search :size="15" /><input v-model="query" placeholder="搜索姓名或学号" aria-label="搜索学生账号" /></label>
                <select v-model="status" aria-label="筛选账号状态">
                  <option value="all">全部状态</option>
                  <option value="enabled">正常使用</option>
                  <option value="disabled">已停用</option>
                </select>
              </div>
            </div>

            <div class="admin-account-table">
              <div class="admin-table-head"><span>学生</span><span>学号</span><span>更新时间</span><span>状态</span><span>操作</span></div>
              <div v-for="account in visibleStudents" :key="account.id" class="admin-account-row">
                <span class="admin-person"><span class="admin-avatar"><UserRound :size="15" /></span><b>{{ account.displayName }}</b></span>
                <span class="admin-mono">{{ account.username }}</span>
                <span class="admin-time">{{ formatTime(account.updatedAt) }}</span>
                <span><i :class="account.enabled ? 'enabled' : 'disabled'">{{ account.enabled ? '正常' : '停用' }}</i></span>
                <span class="admin-row-actions">
                  <button type="button" @click="openReset(account)"><KeyRound :size="14" />重置密码</button>
                  <button type="button" :class="{ danger: account.enabled }" @click="toggleAccount(account)">{{ account.enabled ? '停用' : '启用' }}</button>
                </span>
              </div>
              <div v-if="loading && !students.length" class="admin-empty">正在读取账号数据...</div>
              <div v-else-if="!visibleStudents.length" class="admin-empty">没有符合条件的学生账号。</div>
            </div>

            <footer v-if="filteredStudents.length > PAGE_SIZE" class="admin-pagination">
              <span>第 {{ page }} / {{ pageCount }} 页</span>
              <div>
                <button type="button" aria-label="上一页" :disabled="page === 1" @click="page--"><ChevronLeft :size="16" /></button>
                <button type="button" aria-label="下一页" :disabled="page === pageCount" @click="page++"><ChevronRight :size="16" /></button>
              </div>
            </footer>
          </div>

          <aside class="admin-university-panel">
            <div class="admin-university-title"><span><Building2 :size="19" /></span><div><h2>高校端账号</h2><p>统一入口，仅在需要时修改</p></div></div>
            <form @submit.prevent="saveUniversity">
              <label><span>登录账号</span><input v-model="university.username" required maxlength="64" /></label>
              <label><span>设置新密码</span><input v-model="university.password" type="password" required minlength="6" maxlength="72" placeholder="至少 6 位" /></label>
              <button class="admin-primary" type="submit" :disabled="loading">保存高校账号</button>
            </form>
            <p class="admin-helper">保存后会清除高校端现有登录会话。</p>
          </aside>
        </section>
      </div>

      <div v-if="resetTarget" class="admin-dialog-backdrop" @click.self="resetTarget = null">
        <form class="admin-reset-dialog" role="dialog" aria-modal="true" :aria-label="`重置${resetTarget.displayName}的密码`" @submit.prevent="submitReset">
          <div class="admin-dialog-icon"><KeyRound :size="20" /></div>
          <h2>重置学生密码</h2>
          <p>{{ resetTarget.displayName }}，{{ resetTarget.username }}</p>
          <label><span>新密码</span><input v-model="resetPassword" type="password" required minlength="6" maxlength="72" autofocus placeholder="6-72 位" /></label>
          <div class="admin-dialog-actions"><button type="button" @click="resetTarget = null">取消</button><button class="admin-primary" type="submit" :disabled="loading">确认重置</button></div>
        </form>
      </div>
    </template>
  </main>
</template>
