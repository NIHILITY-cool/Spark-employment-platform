export async function useAuthenticatedSession(page, role, studentId = 1) {
  const account = {
    id: role === 'STUDENT' ? 10 : 20,
    role,
    username: role === 'STUDENT' ? 'demo001' : 'university',
    displayName: role === 'STUDENT' ? '林同学' : '高校就业中心',
    studentId: role === 'STUDENT' ? studentId : null,
    enabled: true,
  }
  await page.addInitScript(({ session }) => {
    localStorage.setItem('employment-auth-session', JSON.stringify(session))
  }, { session: { token: 'playwright-token', account } })
  return account
}
