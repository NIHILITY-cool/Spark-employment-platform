const AUTH_STORAGE_KEY = 'employment-auth-session'
const REQUEST_TIMEOUT_MS = 15_000

export function getAuthSession() {
  try {
    return JSON.parse(localStorage.getItem(AUTH_STORAGE_KEY) || 'null')
  } catch {
    return null
  }
}

export function saveAuthSession(session) {
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session))
}

export function clearAuthSession() {
  localStorage.removeItem(AUTH_STORAGE_KEY)
}

export async function authorizedFetch(url, { timeoutMs = REQUEST_TIMEOUT_MS, signal, ...options } = {}) {
  const token = getAuthSession()?.token
  const controller = new AbortController()
  const abortRequest = () => controller.abort()
  const timeout = setTimeout(abortRequest, timeoutMs)

  if (signal) {
    if (signal.aborted) abortRequest()
    else signal.addEventListener('abort', abortRequest, { once: true })
  }

  try {
    return await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
      },
    })
  } finally {
    clearTimeout(timeout)
    signal?.removeEventListener('abort', abortRequest)
  }
}

export async function apiRequest(baseUrl, path, options = {}) {
  let response
  try {
    response = await authorizedFetch(`${baseUrl}${path}`, {
      ...options,
      headers: {
        ...(options.body ? { 'Content-Type': 'application/json' } : {}),
        ...options.headers,
      },
    })
  } catch (error) {
    if (error?.name === 'AbortError') throw new Error('请求超时，请检查网络连接后重试')
    throw error
  }

  if (!response.ok) {
    let message = `请求失败 (${response.status})`
    try {
      const payload = await response.json()
      message = payload.message || payload.detail || message
    } catch {
      // Keep the status-based message when the server returns no JSON body.
    }
    throw new Error(message)
  }

  return response.status === 204 ? null : response.json()
}
