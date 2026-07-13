export async function apiRequest(baseUrl, path, options = {}) {
  const response = await fetch(`${baseUrl}${path}`, {
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
