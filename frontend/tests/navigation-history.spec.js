import { expect, test } from '@playwright/test'
import { useAuthenticatedSession } from './auth-helper.js'

const pageOneJobs = Array.from({ length: 12 }, (_, index) => ({
  jobKey: `page-one-${index + 1}`, jobName: `数据工程师 ${index + 1}`, companyName: '测试公司', city: '成都',
  jobCategory: '大数据开发', salaryMin: 8000, salaryMax: 14000, educationRequirement: '本科', experienceRequirement: '经验不限', industry: '软件',
}))
const pageTwoJobs = Array.from({ length: 12 }, (_, index) => ({
  jobKey: `page-two-${index + 1}`, jobName: `后端工程师 ${index + 13}`, companyName: '测试公司', city: '北京',
  jobCategory: '后端开发', salaryMin: 9000, salaryMax: 16000, educationRequirement: '本科', experienceRequirement: '1-3年', industry: '软件',
}))

async function mockApi(page) {
  await page.route((url) => url.pathname.startsWith('/api/'), async (route) => {
    const requestUrl = route.request().url()
    if (requestUrl.includes('/auth/me')) await route.fulfill({ json: { id: 10, role: 'STUDENT', username: 'demo001', displayName: '林同学', studentId: 1, enabled: true } })
    else if (requestUrl.includes('/market/statistics/hot_skills')) await route.fulfill({ json: [] })
    else if (requestUrl.includes('/jobs/filters')) await route.fulfill({ json: { cities: ['成都', '北京'], categories: ['大数据开发', '后端开发'] } })
    else if (requestUrl.includes('/jobs?')) {
      const requestedPage = Number(new URL(requestUrl).searchParams.get('page'))
      await route.fulfill({ json: { page: requestedPage, size: 12, total: 25, records: requestedPage === 2 ? pageTwoJobs : pageOneJobs } })
    } else await route.fulfill({ json: [] })
  })
}

test('login failure restores the form instead of leaving it in a validating state', async ({ page }) => {
  await page.route((url) => url.pathname.includes('/api/auth/login'), async (route) => {
    await route.fulfill({ status: 401, json: { message: '账号或密码不正确' } })
  })
  await page.goto('/')
  await page.getByRole('button', { name: '进入学生端' }).click()
  await expect(page).toHaveURL(/\/login\/student$/)
  await page.getByPlaceholder('请输入学号').fill('2026001')
  await page.getByPlaceholder('请输入密码').fill('wrong-password')
  const submit = page.getByRole('button', { name: /进入工作台/ })
  await submit.click()
  await expect(page.locator('.auth-error')).toHaveText('账号或密码不正确')
  await expect(submit).toBeEnabled()
  await expect(submit).toHaveText(/进入工作台/)
})

test('browser history, refresh, and market pagination retain the current view and position', async ({ page }) => {
  await mockApi(page)
  await useAuthenticatedSession(page, 'STUDENT')
  await page.goto('/student/market?page=2')
  await expect(page.getByText('后端工程师 13')).toBeVisible()
  await expect(page).toHaveURL(/\/student\/market\?page=2$/)

  await page.reload()
  await expect(page.getByText('后端工程师 13')).toBeVisible()

  await page.getByRole('button', { name: '技能信号', exact: true }).click()
  await expect(page).toHaveURL(/\/student\/skills$/)
  await page.goBack()
  await expect(page).toHaveURL(/\/student\/market\?page=2$/)
  await expect(page.getByText('后端工程师 13')).toBeVisible()

  await page.evaluate(() => window.scrollTo(0, 360))
  const scrollBefore = await page.evaluate(() => window.scrollY)
  await page.getByRole('button', { name: '上一页岗位' }).evaluate((button) => button.click())
  await expect(page.getByText('数据工程师 1', { exact: true })).toBeVisible()
  expect(await page.evaluate(() => window.scrollY)).toBeGreaterThanOrEqual(scrollBefore - 2)
})
