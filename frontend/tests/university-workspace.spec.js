import { expect, test } from '@playwright/test'

const analysis = {
  statDate: '2026-07-11',
  major: '数据科学与大数据技术',
  targetCategory: '大数据开发',
  city: '',
  availableMajors: {
    数据科学与大数据技术: '大数据开发',
    计算机科学与技术: '后端开发',
    软件工程: '前端开发',
    统计学: '数据分析',
    人工智能: '人工智能',
  },
  summary: { jobCount: 286, entryFriendlyCount: 192, averageSalaryMin: 8200, averageSalaryMax: 13800, extractedSkillCount: 5 },
  cities: [{ key: '北京', jobCount: 62 }, { key: '成都', jobCount: 48 }],
  industries: [{ key: '计算机软件', jobCount: 96 }, { key: '互联网', jobCount: 74 }, { key: '制造业', jobCount: 31 }],
  education: [{ key: '本科及以上', jobCount: 220 }, { key: '硕士及以上', jobCount: 41 }, { key: '不限', jobCount: 25 }],
  skills: [{ key: 'SQL', jobCount: 140 }, { key: 'Python', jobCount: 120 }, { key: 'Spark', jobCount: 88 }, { key: 'Java', jobCount: 65 }, { key: 'Hadoop', jobCount: 52 }],
  regionalMatrix: [
    { city: '北京', category: '大数据开发', jobCount: 62 }, { city: '北京', category: '后端开发', jobCount: 115 },
    { city: '成都', category: '大数据开发', jobCount: 48 }, { city: '成都', category: '后端开发', jobCount: 73 },
    { city: '上海', category: '大数据开发', jobCount: 40 }, { city: '上海', category: '后端开发', jobCount: 96 },
  ],
  suggestions: ['优先评估 SQL、Python、Spark 是否已覆盖在课程或项目训练中。', '该方向岗位主要集中在北京、成都、上海，可作为校企合作区域参考。'],
  dataBasis: '基于 Spark 清洗后写入 MySQL 的 2026-07-11 公开岗位批次；仅反映近期市场需求，不代表培养质量或长期预测。',
}

async function mockApi(page) {
  await page.route('**/api/**', async (route) => {
    const url = route.request().url()
    if (!new URL(url).pathname.startsWith('/api/')) {
      await route.continue()
      return
    }
    if (url.includes('/university/training-alignment')) {
      const requestUrl = new URL(url)
      await route.fulfill({ json: { ...analysis, city: requestUrl.searchParams.get('city') || '' } })
    } else if (url.includes('/jobs/filters')) {
      await route.fulfill({ json: { cities: ['北京', '成都', '上海'], categories: ['大数据开发', '后端开发'] } })
    } else if (url.includes('/jobs?')) {
      await route.fulfill({ json: { page: 1, size: 12, total: 0, records: [] } })
    } else {
      await route.fulfill({ json: [] })
    }
  })
}

test('university training scenario controls update the evidence view', async ({ page }) => {
  await mockApi(page)
  await page.goto('/')
  await page.getByTitle('高校培养参考').click()
  await expect(page.getByRole('heading', { name: '从市场需求反推训练重点。' })).toBeVisible()
  await expect(page.getByText('286')).toBeVisible()

  const coverage = page.locator('.coverage-display strong')
  const initialCoverage = Number((await coverage.textContent()).replace('%', ''))
  await page.getByRole('button', { name: /Java/ }).click()
  const updatedCoverage = Number((await coverage.textContent()).replace('%', ''))
  expect(updatedCoverage).toBeGreaterThan(initialCoverage)

  await page.getByLabel('地区范围').selectOption('成都')
  await page.getByRole('button', { name: /更新分析/ }).click()
  await expect(page.getByText('地区 × 岗位方向需求矩阵')).toBeVisible()
  await expect(page.locator('.matrix-cell')).toHaveCount(6)
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
  expect(overflow).toBeLessThanOrEqual(1)
  await page.screenshot({ path: '/tmp/university-workspace-desktop.png', fullPage: true })
})

test('university evidence view is contained on mobile', async ({ page }) => {
  await mockApi(page)
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await page.getByTitle('高校培养参考').click()
  await expect(page.getByText('计划强化技能组合')).toBeVisible()
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
  expect(overflow).toBeLessThanOrEqual(1)
  await page.screenshot({ path: '/tmp/university-workspace-mobile.png', fullPage: true })
})
