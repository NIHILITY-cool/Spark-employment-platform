import { expect, test } from '@playwright/test'

test('student can register with student number, name and password', async ({ page }) => {
  await page.route((url) => url.pathname.startsWith('/api/'), async (route) => {
    const url = route.request().url()
    if (url.includes('/auth/student/register')) await route.fulfill({ status: 201, json: { token: 'student-token', expiresAt: '2026-07-21T12:00:00', account: { id: 31, role: 'STUDENT', username: '2026008', displayName: '陈同学', studentId: 8, enabled: true } } })
    else if (url.includes('/market/statistics/hot_skills')) await route.fulfill({ json: [] })
    else if (url.includes('/jobs/filters')) await route.fulfill({ json: { cities: [], categories: [] } })
    else if (url.includes('/jobs?')) await route.fulfill({ json: { page: 1, size: 12, total: 0, records: [] } })
    else await route.fulfill({ json: [] })
  })
  await page.goto('/')
  await page.getByRole('button', { name: '进入学生端' }).click()
  await page.getByRole('tab', { name: '注册' }).click()
  await page.getByPlaceholder('请输入学号').fill('2026008')
  await page.getByPlaceholder('请输入真实姓名').fill('陈同学')
  await page.getByPlaceholder('至少 6 位').fill('student1024')
  await page.getByRole('button', { name: /注册并进入/ }).click()
  await expect(page.getByRole('heading', { name: /找到下一份/ })).toBeVisible()
})

test('admin route manages accounts without appearing in the portal', async ({ page }) => {
  const accounts = [
    { id: 2, role: 'UNIVERSITY', username: 'university', displayName: '高校就业中心', studentId: null, enabled: true, updatedAt: '2026-07-14T12:00:00' },
    { id: 3, role: 'STUDENT', username: '2026001', displayName: '林同学', studentId: 1, enabled: true, updatedAt: '2026-07-14T13:00:00' },
  ]
  await page.route((url) => url.pathname.startsWith('/api/'), async (route) => {
    const url = route.request().url()
    if (url.includes('/auth/login')) await route.fulfill({ json: { token: 'admin-token', account: { id: 1, role: 'ADMIN', username: 'admin', displayName: '系统管理员', studentId: null, enabled: true } } })
    else if (url.includes('/admin/accounts')) await route.fulfill({ json: accounts })
    else await route.fulfill({ status: 204, body: '' })
  })
  await page.goto('/admin')
  await expect(page.getByRole('heading', { name: '账号管理' })).toBeVisible()
  await page.getByLabel('管理员密码').fill('1024')
  await page.getByRole('button', { name: /进入管理端/ }).click()
  await expect(page.getByRole('heading', { name: /只管理身份/ })).toBeVisible()
  await expect(page.getByText('林同学', { exact: true })).toBeVisible()
})
