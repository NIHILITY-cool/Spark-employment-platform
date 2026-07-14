import { expect, test } from '@playwright/test'

const skills = [
  { dimensionKey: 'Python', metricValue: 841 }, { dimensionKey: 'Java', metricValue: 782 },
  { dimensionKey: 'SQL', metricValue: 669 }, { dimensionKey: 'Spark', metricValue: 315 },
  { dimensionKey: 'Hive', metricValue: 274 }, { dimensionKey: 'Docker', metricValue: 211 },
  { dimensionKey: 'Kafka', metricValue: 196 }, { dimensionKey: 'Linux', metricValue: 181 },
  { dimensionKey: 'Flink', metricValue: 168 }, { dimensionKey: 'Git', metricValue: 152 },
]

const pageOneJobs = Array.from({ length: 12 }, (_, index) => ({
  jobKey: `page-one-${index + 1}`, jobName: `数据工程师 ${index + 1}`, companyName: '测试公司', city: '成都',
  jobCategory: '大数据开发', salaryMin: 8000, salaryMax: 14000, educationRequirement: '本科', experienceRequirement: '经验不限', industry: '软件',
}))
const pageTwoJobs = Array.from({ length: 12 }, (_, index) => ({
  jobKey: `page-two-${index + 1}`, jobName: `后端工程师 ${index + 13}`, companyName: '测试公司', city: '北京',
  jobCategory: '后端开发', salaryMin: 9000, salaryMax: 16000, educationRequirement: '本科', experienceRequirement: '1-3年', industry: '软件',
}))

const regionDashboard = {
  statDate: '2026-07-11',
  summary: { jobCount: 12000, companyCount: 4835, cityCount: 190, industryCount: 15, averageSalary: 9200, entryFriendlyCount: 7600 },
  provinceDemand: [
    { key: '广东', jobCount: 1680, averageSalaryMin: 8600, averageSalaryMax: 14800 },
    { key: '四川', jobCount: 920, averageSalaryMin: 7200, averageSalaryMax: 12100 },
  ],
  cities: [{ key: '深圳', jobCount: 760 }, { key: '广州', jobCount: 620 }, { key: '东莞', jobCount: 180 }],
  industries: [{ key: '信息技术', jobCount: 720 }, { key: '智能制造', jobCount: 430 }],
  jobCategories: [{ key: '软件开发', jobCount: 520 }, { key: '数据分析', jobCount: 310 }],
}

async function mockMarketApi(page) {
  await page.route((url) => url.pathname.startsWith('/api/'), async (route) => {
    const url = route.request().url()
    if (url.includes('/university/market-dashboard')) {
      const province = new URL(url).searchParams.get('city')
      await route.fulfill({ json: province ? { ...regionDashboard, filter: { city: province }, summary: { ...regionDashboard.summary, jobCount: 1680, entryFriendlyCount: 1120 } } : regionDashboard })
    }
    else if (url.includes('/market/statistics/hot_skills')) await route.fulfill({ json: skills })
    else if (url.includes('/jobs/filters')) await route.fulfill({ json: { cities: ['成都', '北京', '上海', '重庆'], categories: ['大数据开发', '后端开发', '数据分析'] } })
    else if (url.includes('/jobs?')) {
      const pageNumber = Number(new URL(url).searchParams.get('page'))
      await route.fulfill({ json: { page: pageNumber, size: 12, total: 25, records: pageNumber === 2 ? pageTwoJobs : pageOneJobs } })
    }
    else if (url.includes('/jobs/')) {
      await route.fulfill({ json: {
        job: { ...pageOneJobs[0], district: '高新区', companyScale: '100-499人', sourceName: 'ncss', lastSeenDate: '2026-07-11', jobUrl: 'https://example.com/job/page-one-1', jobDescription: '负责数据处理任务开发，参与数据平台建设与维护。' },
        skills: [{ skillName: 'Python' }, { skillName: 'Spark' }, { skillName: 'SQL' }],
      } })
    }
    else await route.fulfill({ json: [] })
  })
}

test('skills signal is a separate student market page with interactive analysis', async ({ page }, testInfo) => {
  await mockMarketApi(page)
  await page.goto('/')
  await page.getByRole('button', { name: '进入学生端' }).click()
  await expect(page.getByRole('heading', { name: /找到下一份/ })).toBeVisible()

  await page.getByRole('button', { name: '技能信号', exact: true }).click()
  await expect(page.getByRole('heading', { name: '市场技能排名' })).toBeVisible()
  await expect(page.locator('.job-zone')).toHaveCount(0)
  await expect(page.locator('.skill-signal')).toHaveCount(8)
  await expect(page.locator('.city-demand-section')).toHaveCount(0)

  await page.locator('.skill-signal').filter({ hasText: 'Java' }).click()
  await expect(page.locator('.skill-focus-panel h2')).toHaveText('Java')
  await page.getByRole('button', { name: '下一页技能信号' }).click()
  await expect(page.locator('.skill-signal')).toHaveCount(2)
  await expect(page.locator('.skill-signal').filter({ hasText: 'Flink' })).toBeVisible()
  await page.screenshot({ path: testInfo.outputPath('skills-page-desktop.png'), fullPage: true })
})

test('student region page drills from province opportunities into city jobs', async ({ page }, testInfo) => {
  await mockMarketApi(page)
  await page.goto('/')
  await page.getByRole('button', { name: '进入学生端' }).click()
  await page.getByRole('button', { name: '地区分布', exact: true }).click()

  await expect(page.getByRole('heading', { name: /先看机会在哪/ })).toBeVisible()
  await expect(page.locator('.student-region-map canvas')).toBeVisible()
  await expect(page.getByText('深圳', { exact: true })).toBeVisible()
  await expect(page.getByText('软件开发', { exact: true })).toBeVisible()
  await page.screenshot({ path: testInfo.outputPath('student-region-desktop.png'), fullPage: true })

  await page.getByRole('button', { name: /深圳/ }).click()
  await expect(page.getByRole('heading', { name: /从市场里挑选方向/ })).toBeVisible()
  await expect(page.getByRole('combobox', { name: '搜索或选择城市' })).toHaveValue('深圳')
})

test('student region page stays contained on mobile', async ({ page }, testInfo) => {
  await mockMarketApi(page)
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await page.getByRole('button', { name: '进入学生端' }).click()
  await page.getByRole('tab', { name: '地区分布' }).click()
  await expect(page.locator('.student-region-map canvas')).toBeVisible()
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
  expect(overflow).toBeLessThanOrEqual(1)
  await page.screenshot({ path: testInfo.outputPath('student-region-mobile.png'), fullPage: true })
})

test('student market requests a new backend page instead of expanding all jobs', async ({ page }) => {
  await mockMarketApi(page)
  await page.goto('/')
  await page.getByRole('button', { name: '进入学生端' }).click()
  await expect(page.locator('.job-card')).toHaveCount(12)
  await expect(page.getByText('第 1 / 3 页')).toBeVisible()

  await page.getByRole('button', { name: '下一页岗位' }).click()
  await expect(page.getByText('第 2 / 3 页')).toBeVisible()
  await expect(page.getByText('后端工程师 13')).toBeVisible()
})

test('clicking a job opens a detailed in-page job drawer', async ({ page }) => {
  await mockMarketApi(page)
  await page.goto('/')
  await page.getByRole('button', { name: '进入学生端' }).click()
  await page.getByText('数据工程师 1', { exact: true }).click()

  const dialog = page.getByRole('dialog', { name: '数据工程师 1岗位详情' })
  await expect(dialog).toBeVisible()
  await expect(dialog.getByText('负责数据处理任务开发，参与数据平台建设与维护。')).toBeVisible()
  await expect(dialog.getByRole('heading', { name: '岗位技能' })).toHaveCount(0)
  await expect(dialog.getByText('Python', { exact: true })).toHaveCount(0)
  await expect(dialog.getByRole('link', { name: '打开原岗位链接' })).toHaveAttribute('href', 'https://example.com/job/page-one-1')
  await dialog.getByRole('button', { name: '关闭岗位详情' }).click()
  await expect(dialog).toHaveCount(0)
})

test('student market selectors use the shared searchable picker on mobile', async ({ page }, testInfo) => {
  await mockMarketApi(page)
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await page.getByRole('button', { name: '进入学生端' }).click()
  await page.getByRole('tab', { name: '技能信号' }).click()
  await expect(page.getByRole('heading', { name: '市场技能排名' })).toBeVisible()
  await page.screenshot({ path: testInfo.outputPath('skills-page-mobile.png'), fullPage: true })

  await page.getByRole('tab', { name: '岗位市场' }).click()
  const cityPicker = page.getByRole('combobox', { name: '搜索或选择城市' })
  await cityPicker.fill('成都')
  await page.getByRole('option', { name: '成都', exact: true }).click()
  await expect(cityPicker).toHaveValue('成都')
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
  expect(overflow).toBeLessThanOrEqual(1)
})
