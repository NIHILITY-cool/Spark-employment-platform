import { expect, test } from '@playwright/test'

test('role landing keeps student and university workspaces separated', async ({ page }, testInfo) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: /选择你的\s*工作台/ })).toBeVisible()
  await page.screenshot({ path: testInfo.outputPath('role-landing-desktop.png'), fullPage: true })

  await page.getByRole('button', { name: '进入学生端' }).click()
  await expect(page.getByRole('heading', { name: '学生登录' })).toBeVisible()
  await expect(page.getByRole('button', { name: '进入高校端' })).toHaveCount(0)
  await page.getByRole('button', { name: '返回入口' }).click()

  await page.getByRole('button', { name: '进入高校端' }).click()
  await expect(page.getByRole('heading', { name: '高校登录' })).toBeVisible()
  await expect(page.getByRole('button', { name: '岗位市场' })).toHaveCount(0)
})

test('role landing remains contained on mobile', async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await expect(page.getByRole('heading', { name: /选择你的\s*工作台/ })).toBeVisible()
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
  expect(overflow).toBeLessThanOrEqual(1)
  await page.screenshot({ path: testInfo.outputPath('role-landing-mobile.png'), fullPage: true })
})
