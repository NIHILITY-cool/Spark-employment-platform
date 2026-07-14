import { expect, test } from '@playwright/test'

const profilePayload = {
  profile: { studentNo: 'demo001', name: '林同学', college: '计算机学院', major: '数据科学与大数据技术', education: '本科', graduationYear: 2027 },
  preference: { expectedJob: '大数据开发', expectedCity: '成都', expectedIndustry: '软件', salaryMin: 8000, salaryMax: 13000, acceptRemoteCity: true },
  skills: [
    ['Python', 4], ['SQL', 4], ['Spark', 3], ['Java', 3],
    ['Hadoop', 3], ['Vue', 2], ['Git', 4], ['MySQL', 4],
  ].map(([skillName, skillLevel], index) => ({ id: index + 1, skillName, skillLevel })),
}

const recommendations = Array.from({ length: 10 }, (_, index) => ({
  totalScore: 86 - index,
  skillScore: 32,
  experienceScore: 15,
  directionScore: 14,
  educationScore: 10,
  cityScore: 10,
  industryScore: 4,
  salaryScore: 5,
  recencyScore: 4,
  matchedSkills: ['Python', 'SQL'],
  matchedExperienceTerms: ['数据', '开发'],
  missingSkills: index % 2 ? ['Spark'] : [],
  recommendationReason: '专业方向、城市和薪资均匹配，已覆盖部分核心技能。',
  job: {
    jobKey: `recommendation-${index + 1}`,
    jobName: `数据开发工程师 ${index + 1}`,
    companyName: '测试科技',
    city: '成都',
    salaryMin: 9000,
    salaryMax: 14000,
    educationRequirement: '本科',
    experienceRequirement: '经验不限',
    jobUrl: 'https://example.com/job',
  },
}))

async function mockStudentApi(page) {
  await page.route((url) => url.pathname.startsWith('/api/'), async (route) => {
    const requestUrl = route.request().url()
    if (requestUrl.includes('/students/1/profile')) await route.fulfill({ json: profilePayload })
    else if (requestUrl.includes('/recommendations/top10')) await route.fulfill({ json: recommendations })
    else if (requestUrl.includes('/recommendations/skill-gap')) await route.fulfill({ json: { masteredSkills: ['Python', 'SQL'], missingSkills: ['Spark'], suggestion: '建议补强 Spark 项目实践。' } })
    else if (requestUrl.includes('/jobs/filters')) await route.fulfill({ json: { cities: ['成都', '北京'], categories: ['大数据开发', '后端开发'] } })
    else if (requestUrl.includes('/jobs?')) await route.fulfill({ json: { page: 1, size: 12, total: 1, records: [{ jobKey: 'job-1', jobName: '大数据开发工程师', companyName: '测试科技', city: '成都', jobCategory: '大数据开发', salaryMin: 9000, salaryMax: 14000, educationRequirement: '本科', experienceRequirement: '经验不限', industry: '软件' }] } })
    else await route.fulfill({ json: [] })
  })
}

test('student profile and recommendation workflow is interactive', async ({ page }, testInfo) => {
  await mockStudentApi(page)
  await page.goto('/')
  await expect(page.getByRole('heading', { name: /从你的视角/ })).toBeVisible()
  await page.getByRole('button', { name: '进入学生端' }).click()
  await expect(page.getByRole('heading', { name: /找到下一份/ })).toBeVisible()

  const favorite = page.getByRole('button', { name: '收藏岗位' }).first()
  await favorite.click()
  await expect(favorite).toHaveAttribute('aria-pressed', 'true')

  await page.getByRole('button', { name: /我的工作台/ }).click()
  await expect(page.getByRole('heading', { name: /把目标变成下一步行动/ })).toBeVisible()
  await page.getByRole('tab', { name: /画像与期望/ }).click()
  await expect(page.getByRole('heading', { name: '个人信息' })).toBeVisible()
  await expect(page.getByRole('heading', { name: '实践与成果' })).toBeVisible()
  await expect(page.getByText('Python', { exact: true }).first()).toBeVisible()
  await expect(page.locator('.skill-row')).toHaveCount(7)
  await page.getByTitle('下一页技能').click()
  await expect(page.locator('.skill-row')).toHaveCount(1)
  await page.getByTitle('上一页技能').click()
  await page.getByRole('button', { name: '开始时间' }).click()
  await expect(page.getByRole('dialog', { name: '开始时间日期选择' })).toBeVisible()
  await page.screenshot({ path: '/tmp/student-date-picker.png', fullPage: true })
  await page.keyboard.press('Escape')
  const profileOverflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
  expect(profileOverflow).toBeLessThanOrEqual(1)
  await page.screenshot({ path: testInfo.outputPath('student-profile-desktop.png'), fullPage: true })

  await page.getByRole('tab', { name: /Top10 推荐/ }).click()
  const recommendations = page.locator('.recommendation-row')
  await expect(recommendations.first()).toBeVisible()
  expect(await recommendations.count()).toBeLessThanOrEqual(10)
  await recommendations.first().locator('.recommendation-summary').click()
  await expect(recommendations.first().getByText('推荐依据')).toBeVisible()
  await expect(recommendations.first().getByText('经历命中', { exact: true })).toBeVisible()
  await expect(recommendations.first().locator('.score-track > div')).toHaveCount(6)

  await page.screenshot({ path: testInfo.outputPath('student-workspace-desktop.png'), fullPage: true })
})

test('student workspace remains usable on a mobile viewport', async ({ page }, testInfo) => {
  await mockStudentApi(page)
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await page.getByRole('button', { name: '进入学生端' }).click()
  await page.getByRole('button', { name: /我的工作台/ }).click()
  await expect(page.getByRole('heading', { name: /把目标变成下一步行动/ })).toBeVisible()

  await page.getByRole('tab', { name: /画像与期望/ }).click()
  await expect(page.getByRole('heading', { name: '实践与成果' })).toBeVisible()

  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
  expect(overflow).toBeLessThanOrEqual(1)
  await page.screenshot({ path: testInfo.outputPath('student-workspace-mobile.png'), fullPage: true })
})
