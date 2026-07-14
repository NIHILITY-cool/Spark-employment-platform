import { expect, test } from '@playwright/test'

test('student profile and recommendation workflow is interactive', async ({ page }) => {
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
  await page.screenshot({ path: '/tmp/student-profile-desktop.png', fullPage: true })

  await page.getByRole('tab', { name: /Top10 推荐/ }).click()
  const recommendations = page.locator('.recommendation-row')
  await expect(recommendations.first()).toBeVisible()
  expect(await recommendations.count()).toBeLessThanOrEqual(10)
  await recommendations.first().getByRole('button').first().click()
  await expect(recommendations.first().getByText('推荐依据')).toBeVisible()
  await expect(recommendations.first().getByText('经历命中', { exact: true })).toBeVisible()
  await expect(recommendations.first().locator('.score-track > div')).toHaveCount(6)

  await page.screenshot({ path: '/tmp/student-workspace-desktop.png', fullPage: true })
})

test('student workspace remains usable on a mobile viewport', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await page.getByRole('button', { name: '进入学生端' }).click()
  await page.getByRole('button', { name: /我的工作台/ }).click()
  await expect(page.getByRole('heading', { name: /把目标变成下一步行动/ })).toBeVisible()

  await page.getByRole('tab', { name: /画像与期望/ }).click()
  await expect(page.getByRole('heading', { name: '实践与成果' })).toBeVisible()

  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
  expect(overflow).toBeLessThanOrEqual(1)
  await page.screenshot({ path: '/tmp/student-workspace-mobile.png', fullPage: true })
})
