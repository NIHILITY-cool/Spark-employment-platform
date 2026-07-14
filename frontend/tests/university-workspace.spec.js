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

const dashboard = {
  statDate: '2026-07-11',
  filter: {},
  summary: { jobCount: 12000, companyCount: 7300, cityCount: 86, industryCount: 42, averageSalary: 8840, medianSalary: 7600, maxSalary: 45000, entryFriendlyCount: 8300, skillJobCount: 2505 },
  cities: [{ key: '北京', jobCount: 722, averageSalaryMin: 9800, averageSalaryMax: 16000 }, { key: '成都', jobCount: 705, averageSalaryMin: 7600, averageSalaryMax: 12800 }],
  industries: [{ key: '计算机软件', jobCount: 645 }, { key: '教育/培训/院校', jobCount: 1045 }],
  education: [{ key: '本科及以上', jobCount: 4194 }, { key: '专科及以上', jobCount: 4651 }],
  companyScales: [{ key: '100-499人', jobCount: 2800 }, { key: '20-99人', jobCount: 2400 }],
  jobCategories: [{ key: '软件开发', jobCount: 1180 }, { key: '数据分析', jobCount: 840 }],
  hotJobs: [{ key: '软件开发工程师', jobCount: 128, averageSalaryMin: 9000, averageSalaryMax: 15000 }],
  hotSkills: [{ key: 'Python', jobCount: 841 }, { key: 'Java', jobCount: 782 }, { key: 'SQL', jobCount: 669 }],
  salaryBuckets: [{ key: '5k-8k', jobCount: 4800 }, { key: '8k-12k', jobCount: 3100 }],
  categoryFamilies: [
    { family: '技术研发', jobCount: 3180, typicalJobs: ['软件开发', '算法', '测试', '运维', '硬件工程师'], rule: '产出代码、技术方案或产品原型', categories: [{ key: '软件开发', jobCount: 1180 }] },
    { family: '产品运营', jobCount: 1860, typicalJobs: ['产品经理', '用户运营', '数据分析', '项目管理'], rule: '围绕产品生命周期，连接技术与市场', categories: [{ key: '数据分析', jobCount: 840 }] },
  ],
  regionalCategoryShares: [
    { city: '北京', jobCount: 722, categories: [{ key: '技术研发', jobCount: 260 }, { key: '产品运营', jobCount: 180 }] },
    { city: '成都', jobCount: 705, categories: [{ key: '技术研发', jobCount: 220 }, { key: '产品运营', jobCount: 160 }] },
  ],
  cityIndustryHeatmap: [{ x: '北京', y: '计算机软件', jobCount: 150 }, { x: '成都', y: '教育/培训/院校', jobCount: 96 }],
  suggestions: ['岗位需求集中在北京、成都，建议将这些地区作为就业信息推送和校企合作重点。'],
  dataQuality: {
    statDate: '2026-07-11',
    source: 'NCSS、国聘、猎聘、智联公开岗位',
    rawRecordCount: 12025,
    cleanedRecordCount: 12000,
    excludedRecordCount: 25,
    duplicateJobIdCount: 0,
    missingFields: [{ key: 'industry', count: 14, rate: 0.12 }],
    exclusionReasons: [{ key: 'hard_experience_requirement', count: 22, rate: 0.18 }],
    salaryParseStatus: [{ key: '已解析', count: 12000, rate: 100 }],
    note: '字段缺失按当前 MySQL 有效岗位批次统计。',
  },
  dataBasis: '基于 Spark 清洗后写入 MySQL 的 2026-07-11 公开岗位批次。',
}

async function mockApi(page) {
  await page.route((url) => url.pathname.startsWith('/api/'), async (route) => {
    const url = route.request().url()
    if (url.includes('/university/market-dashboard')) {
      await route.fulfill({ json: dashboard })
    } else if (url.includes('/university/training-alignment')) {
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
  await page.getByRole('button', { name: '进入高校端' }).click()
  await expect(page.getByRole('heading', { name: '用岗位数据支撑就业指导。' })).toBeVisible()
  await expect(page.getByText('岗位大类归并规则')).toBeVisible()
  await expect(page.getByText('地区岗位结构占比')).toBeVisible()

  await page.getByRole('button', { name: '专业方向' }).click()
  await expect(page.getByRole('heading', { name: '从市场需求反推训练重点。' })).toBeVisible()
  await expect(page.getByText('286')).toBeVisible()

  const coverage = page.locator('.coverage-display strong')
  const initialCoverage = Number((await coverage.textContent()).replace('%', ''))
  await page.getByRole('button', { name: /Java/ }).click()
  const updatedCoverage = Number((await coverage.textContent()).replace('%', ''))
  expect(updatedCoverage).toBeGreaterThan(initialCoverage)

  const cityPicker = page.getByRole('combobox', { name: '地区范围' })
  await cityPicker.fill('成都')
  await page.getByRole('option', { name: '成都', exact: true }).click()
  await expect(cityPicker).toHaveValue('成都')
  await page.getByRole('button', { name: /更新分析/ }).click()
  await expect(page.getByText('地区 × 岗位方向需求矩阵')).toBeVisible()
  await expect(page.locator('.matrix-cell')).toHaveCount(6)
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
  expect(overflow).toBeLessThanOrEqual(1)
})

test('university evidence view is contained on mobile', async ({ page }) => {
  await mockApi(page)
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await page.getByRole('button', { name: '进入高校端' }).click()
  await expect(page.getByText('岗位大类归并规则')).toBeVisible()
  await page.getByRole('button', { name: '专业方向' }).click()
  await expect(page.getByText('计划强化技能组合')).toBeVisible()
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
  expect(overflow).toBeLessThanOrEqual(1)
})
