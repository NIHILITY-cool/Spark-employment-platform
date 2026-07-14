const AUTH_STORAGE_KEY = 'employment-auth-session'

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

export async function authorizedFetch(url, options = {}) {
  const token = getAuthSession()?.token
  return fetch(url, {
    ...options,
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  })
}

export async function apiRequest(baseUrl, path, options = {}) {
  const response = await authorizedFetch(`${baseUrl}${path}`, {
    ...options,
    headers: {
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...options.headers,
    },
  })

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
