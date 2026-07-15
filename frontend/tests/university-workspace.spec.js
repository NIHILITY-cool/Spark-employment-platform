import { expect, test } from '@playwright/test'
import { useAuthenticatedSession } from './auth-helper.js'

const dashboard = {
  statDate: '2026-07-11',
  filter: {},
  summary: { jobCount: 12000, companyCount: 7300, cityCount: 86, industryCount: 42, averageSalary: 8840, medianSalary: 7600, maxSalary: 45000, entryFriendlyCount: 8300, skillJobCount: 2505 },
  provinceDemand: [{ key: '北京', jobCount: 722, averageSalaryMin: 9800, averageSalaryMax: 16000 }, { key: '四川', jobCount: 705, averageSalaryMin: 7600, averageSalaryMax: 12800 }],
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

const industrySalary = {
  statDate: '2026-07-11',
  city: '',
  classificationBasis: '按岗位名称与岗位描述关键词依次匹配；薪资采用月薪上下限中位值，未命中规则的岗位归入其他。',
  industries: [
    ['金融', 80, 76, 12800, 3, 9, 25, 31, 8], ['商贸与消费', 110, 100, 9200, 8, 30, 39, 20, 3],
    ['医药生物', 62, 57, 11500, 2, 10, 21, 20, 4], ['科技', 286, 270, 14800, 4, 18, 82, 121, 45],
    ['制造业', 130, 119, 10500, 7, 27, 52, 29, 4], ['农业与食品', 43, 39, 7800, 6, 15, 12, 5, 1],
    ['服务业', 95, 82, 7600, 15, 32, 25, 9, 1], ['建筑与房地产', 72, 68, 12100, 3, 12, 22, 26, 5],
    ['教育', 66, 61, 9800, 4, 16, 25, 14, 2], ['其他', 30, 25, 8800, 3, 7, 10, 4, 1],
  ].map(([industry, jobCount, salarySampleCount, averageSalary, below5k, from5kTo8k, from8kTo12k, from12kTo20k, above20k]) => (
    { industry, jobCount, salarySampleCount, averageSalary, below5k, from5kTo8k, from8kTo12k, from12kTo20k, above20k }
  )),
}

const studentInsight = {
  summary: { studentCount: 3, profileCompletedCount: 2, difficultCount: 1, averageTopMatchScore: 67 },
  students: [
    { studentId: 3, studentNo: '2026003', name: '周同学', college: '计算机学院', major: '软件工程', education: '本科', graduationYear: 2027, profileCompleted: false, lastSavedAt: '2026-07-14T12:00:00', skillCount: 0, experienceCount: 0, preferenceSaved: false, topMatchScore: 0, averageMatchScore: 0, bestJobName: '', bestJobCategory: '', difficult: true, status: '重点支持', gaps: ['基本画像尚未完善', '技能清单未保存', '缺少项目或实习经历', '未保存就业期望'], evidence: [] },
    { studentId: 1, studentNo: '2026001', name: '林同学', college: '计算机学院', major: '数据科学与大数据技术', education: '本科', graduationYear: 2027, profileCompleted: true, lastSavedAt: '2026-07-14T13:10:00', skillCount: 5, experienceCount: 2, preferenceSaved: true, topMatchScore: 72, averageMatchScore: 65, bestJobName: '大数据开发工程师', bestJobCategory: '大数据开发', difficult: false, status: '匹配较好', gaps: ['实践经历与目标岗位关联偏弱'], evidence: ['已维护 5 项技能', '岗位方向符合期望'] },
  ],
  dataBasis: '学生情况以学生最后一次保存的画像、技能、经历和就业期望为准。',
  page: 1,
  size: 10,
  total: 22,
  totalPages: 3,
}

async function mockApi(page) {
  await page.route((url) => url.pathname.startsWith('/api/'), async (route) => {
    const url = route.request().url()
    if (url.includes('/auth/me')) await route.fulfill({ json: { id: 20, role: 'UNIVERSITY', username: 'university', displayName: '高校就业中心', studentId: null, enabled: true } })
    else if (url.includes('/university/students')) {
      const requestUrl = new URL(url)
      const requestedPage = Number(requestUrl.searchParams.get('page') || 1)
      const pageStudents = requestedPage === 2
        ? [{ ...studentInsight.students[1], studentId: 12, studentNo: '2026012', name: '分页同学' }]
        : studentInsight.students
      await route.fulfill({ json: { ...studentInsight, page: requestedPage, students: pageStudents } })
    }
    else if (url.includes('/university/market-dashboard')) {
      await route.fulfill({ json: dashboard })
    } else if (url.includes('/university/industry-salary-distribution')) {
      const requestUrl = new URL(url)
      await route.fulfill({ json: { ...industrySalary, city: requestUrl.searchParams.get('city') || '' } })
    } else if (url.includes('/jobs/filters')) {
      await route.fulfill({ json: { cities: ['北京', '成都', '上海'], categories: ['大数据开发', '后端开发'] } })
    } else if (url.includes('/jobs?')) {
      await route.fulfill({ json: { page: 1, size: 12, total: 0, records: [] } })
    } else {
      await route.fulfill({ json: [] })
    }
  })
}

test('university market and student controls update the evidence view', async ({ page }, testInfo) => {
  await mockApi(page)
  await useAuthenticatedSession(page, 'UNIVERSITY')
  await page.goto('/')
  await expect(page.getByRole('heading', { name: '用岗位数据支撑就业指导。' })).toBeVisible()
  await expect(page.getByText('地区岗位结构占比')).toBeVisible()

  await page.getByRole('button', { name: '学生情况' }).click()
  await expect(page.getByRole('heading', { name: '优先跟进需要帮助的学生' })).toBeVisible()
  await expect(page.getByText('周同学', { exact: true }).first()).toBeVisible()
  await expect(page.getByText('基本画像尚未完善')).toBeVisible()
  const supportRequest = page.waitForRequest((request) => request.url().includes('/university/students?') && request.url().includes('status=support'))
  await page.getByRole('button', { name: '重点支持', exact: true }).click()
  await supportRequest
  await expect(page.getByText('缺 3–4 项为重点支持')).toBeVisible()
  await expect(page.getByText('匹配分低于 65 为常规跟进')).toBeVisible()
  await page.getByRole('button', { name: '下一页学生' }).click()
  await expect(page.getByText('分页同学', { exact: true }).first()).toBeVisible()

  await page.getByRole('button', { name: '岗位需求' }).click()
  await expect(page.getByText('岗位大类归并规则')).toBeVisible()

  await page.getByRole('button', { name: '薪资技能' }).click()
  await expect(page.getByRole('heading', { name: '十大行业薪资分布' })).toBeVisible()
  await expect(page.locator('.industry-salary-chart canvas')).toBeVisible()
  await page.screenshot({ path: testInfo.outputPath('university-salary-desktop.png'), fullPage: true })

  await expect(page.getByRole('button', { name: '专业方向' })).toHaveCount(0)
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
  expect(overflow).toBeLessThanOrEqual(1)
})

test('university evidence view is contained on mobile', async ({ page }, testInfo) => {
  await mockApi(page)
  await useAuthenticatedSession(page, 'UNIVERSITY')
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await page.getByRole('button', { name: '岗位需求' }).click()
  await expect(page.getByText('岗位大类归并规则')).toBeVisible()
  await page.getByRole('button', { name: '薪资技能' }).click()
  await expect(page.locator('.industry-salary-chart canvas')).toBeVisible()
  await expect(page.getByRole('button', { name: '专业方向' })).toHaveCount(0)
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
  expect(overflow).toBeLessThanOrEqual(1)
  await page.screenshot({ path: testInfo.outputPath('university-evidence-mobile.png'), fullPage: true })
})
