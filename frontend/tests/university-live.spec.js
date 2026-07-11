import { expect, test } from '@playwright/test'

test.skip(process.env.LIVE_API !== '1', 'Set LIVE_API=1 when the virtual machine API is available.')

test('university workspace renders the live Spark/MySQL aggregation', async ({ page }) => {
  await page.goto('/')
  const responsePromise = page.waitForResponse((response) =>
    response.url().includes('/api/university/training-alignment') && response.status() === 200)
  await page.getByTitle('高校培养参考').click()
  const response = await responsePromise
  const payload = await response.json()

  expect(payload.summary.jobCount).toBeGreaterThan(0)
  expect(payload.regionalMatrix.length).toBeGreaterThan(0)
  await expect(page.getByRole('heading', { name: '从市场需求反推训练重点。' })).toBeVisible()
  await expect(page.locator('.evidence-strip strong').first()).toHaveText(payload.summary.jobCount.toLocaleString())
  await expect(page.locator('.demand-skill-list button')).toHaveCount(payload.skills.length)
  await page.screenshot({ path: '/tmp/university-workspace-live.png', fullPage: true })
})
