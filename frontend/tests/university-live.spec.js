import { expect, test } from '@playwright/test'

test.skip(process.env.LIVE_API !== '1', 'Set LIVE_API=1 when the virtual machine API is available.')

test('university workspace renders the live Spark/MySQL aggregation', async ({ page }, testInfo) => {
  await page.goto('/')
  const responsePromise = page.waitForResponse((response) =>
    response.url().includes('/api/university/market-dashboard') && response.status() === 200)
  await page.getByRole('button', { name: '进入高校端' }).click()
  const response = await responsePromise
  const payload = await response.json()

  expect(payload.summary.jobCount).toBeGreaterThan(0)
  expect(payload.regionalCategoryShares.length).toBeGreaterThan(0)
  await expect(page.getByRole('heading', { name: '用岗位数据支撑就业指导。' })).toBeVisible()
  await expect(page.locator('.dashboard-kpis strong').first()).toHaveText(payload.summary.jobCount.toLocaleString())
  await expect(page.getByText('岗位大类归并规则')).toBeVisible()

  const salaryResponsePromise = page.waitForResponse((response) =>
    response.url().includes('/api/university/industry-salary-distribution') && response.status() === 200)
  await page.getByRole('button', { name: '薪资技能' }).click()
  const salaryPayload = await (await salaryResponsePromise).json()
  expect(salaryPayload.industries).toHaveLength(10)
  await expect(page.locator('.industry-salary-chart canvas')).toBeVisible()
  await page.screenshot({ path: testInfo.outputPath('university-workspace-live.png'), fullPage: true })
})
