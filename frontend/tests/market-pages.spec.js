import { expect, test } from '@playwright/test'

const skills = [
  { dimensionKey: 'Python', metricValue: 841 }, { dimensionKey: 'Java', metricValue: 782 },
  { dimensionKey: 'SQL', metricValue: 669 }, { dimensionKey: 'Spark', metricValue: 315 },
  { dimensionKey: 'Hive', metricValue: 274 }, { dimensionKey: 'Docker', metricValue: 211 },
]

async function mockMarketApi(page) {
  await page.route((url) => url.pathname.startsWith('/api/'), async (route) => {
    const url = route.request().url()
    if (url.includes('/market/statistics/city_distribution')) await route.fulfill({ json: [{ dimensionKey: '成都', metricValue: 1255 }, { dimensionKey: '北京', metricValue: 722 }, { dimensionKey: '上海', metricValue: 640 }, { dimensionKey: '重庆', metricValue: 177 }] })
    else if (url.includes('/market/statistics/hot_skills')) await route.fulfill({ json: skills })
    else if (url.includes('/jobs/filters')) await route.fulfill({ json: { cities: ['成都', '北京', '上海', '重庆'], categories: ['大数据开发', '后端开发', '数据分析'] } })
    else if (url.includes('/jobs?')) await route.fulfill({ json: { page: 1, size: 12, total: 0, records: [] } })
    else await route.fulfill({ json: [] })
  })
}

test('skills signal is a separate student market page with interactive analysis', async ({ page }) => {
  await mockMarketApi(page)
  await page.goto('/')
  await page.getByRole('button', { name: '进入学生端' }).click()
  await expect(page.getByRole('heading', { name: /找到下一份/ })).toBeVisible()

  await page.getByRole('button', { name: '技能信号', exact: true }).click()
  await expect(page.getByRole('heading', { name: '市场技能排名' })).toBeVisible()
  await expect(page.locator('.job-zone')).toHaveCount(0)
  await expect(page.locator('.skill-signal')).toHaveCount(skills.length)

  await page.locator('.skill-signal').filter({ hasText: 'Java' }).click()
  await expect(page.locator('.skill-focus-panel h2')).toHaveText('Java')
  await page.screenshot({ path: '/tmp/skills-page-desktop.png', fullPage: true })
})

test('student market selectors use the shared searchable picker on mobile', async ({ page }) => {
  await mockMarketApi(page)
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await page.getByRole('button', { name: '进入学生端' }).click()
  await page.getByRole('tab', { name: '技能信号' }).click()
  await expect(page.getByRole('heading', { name: '市场技能排名' })).toBeVisible()
  await page.screenshot({ path: '/tmp/skills-page-mobile.png', fullPage: true })

  await page.getByRole('tab', { name: '岗位市场' }).click()
  const cityPicker = page.getByRole('combobox', { name: '搜索或选择城市' })
  await cityPicker.fill('成都')
  await page.getByRole('option', { name: '成都', exact: true }).click()
  await expect(cityPicker).toHaveValue('成都')
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
  expect(overflow).toBeLessThanOrEqual(1)
})
