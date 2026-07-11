import { expect, test } from '@playwright/test'

test('role landing keeps student and university workspaces separated', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: /从你的视角/ })).toBeVisible()
  await page.screenshot({ path: '/tmp/role-landing-desktop.png', fullPage: true })

  await page.getByRole('button', { name: '进入学生端' }).click()
  await expect(page.getByRole('heading', { name: /找到下一份/ })).toBeVisible()
  await expect(page.getByRole('button', { name: '进入高校端' })).toHaveCount(0)
  await page.getByTitle('返回身份选择').click()

  await page.getByRole('button', { name: '进入高校端' }).click()
  await expect(page.getByRole('heading', { name: '从市场需求反推训练重点。' })).toBeVisible()
  await expect(page.getByRole('button', { name: '岗位市场' })).toHaveCount(0)
})

test('role landing remains contained on mobile', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await expect(page.getByRole('heading', { name: /从你的视角/ })).toBeVisible()
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
  expect(overflow).toBeLessThanOrEqual(1)
  await page.screenshot({ path: '/tmp/role-landing-mobile.png', fullPage: true })
})
