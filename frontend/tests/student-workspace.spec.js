import { expect, test } from '@playwright/test'

test('student profile and recommendation workflow is interactive', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: /找到下一份/ })).toBeVisible()

  const favorite = page.getByRole('button', { name: '收藏岗位' }).first()
  await favorite.click()
  await expect(favorite).toHaveAttribute('aria-pressed', 'true')

  await page.getByRole('button', { name: /学生入口/ }).click()
  await expect(page.getByRole('heading', { name: /把目标变成下一步行动/ })).toBeVisible()
  await expect(page.getByText('Python', { exact: true }).first()).toBeVisible()
  await page.getByRole('tab', { name: /画像与期望/ }).click()
  await expect(page.getByRole('heading', { name: '个人信息' })).toBeVisible()
  const profileOverflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
  expect(profileOverflow).toBeLessThanOrEqual(1)
  await page.screenshot({ path: '/tmp/student-profile-desktop.png', fullPage: true })

  await page.getByRole('tab', { name: /Top10 推荐/ }).click()
  const recommendations = page.locator('.recommendation-row')
  await expect(recommendations).toHaveCount(10)
  await recommendations.first().getByRole('button').first().click()
  await expect(recommendations.first().getByText('推荐依据')).toBeVisible()

  await page.screenshot({ path: '/tmp/student-workspace-desktop.png', fullPage: true })
})

test('student workspace remains usable on a mobile viewport', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await page.getByRole('button', { name: /学生入口/ }).click()
  await expect(page.getByRole('heading', { name: /把目标变成下一步行动/ })).toBeVisible()

  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
  expect(overflow).toBeLessThanOrEqual(1)
  await page.screenshot({ path: '/tmp/student-workspace-mobile.png', fullPage: true })
})
