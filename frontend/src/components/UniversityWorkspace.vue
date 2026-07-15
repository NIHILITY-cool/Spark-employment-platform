<script setup>
import { computed, defineAsyncComponent, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { BarChart, HeatmapChart, MapChart, RadarChart, SankeyChart, ScatterChart, TreemapChart } from 'echarts/charts'
import { DataZoomComponent, TooltipComponent, VisualMapComponent } from 'echarts/components'
import { GridComponent, LegendComponent, RadarComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import {
  BriefcaseBusiness,
  Building2,
  ChartNoAxesCombined,
  CircleAlert,
  Database,
  GraduationCap,
  Lightbulb,
  LoaderCircle,
  MapPinned,
  RefreshCw,
  Search,
  Sparkles,
  LogOut,
} from '@lucide/vue'
import { apiRequest } from '../api/client'
import chinaGeoJson from '../assets/china.geo.json'
import SearchSelect from './SearchSelect.vue'

const IndustrySalaryPanel = defineAsyncComponent(() => import('./IndustrySalaryPanel.vue'))
const UniversityStudentOverview = defineAsyncComponent(() => import('./UniversityStudentOverview.vue'))

echarts.use([
  BarChart,
  HeatmapChart,
  MapChart,
  RadarChart,
  SankeyChart,
  ScatterChart,
  TreemapChart,
  GridComponent,
  LegendComponent,
  RadarComponent,
  DataZoomComponent,
  TooltipComponent,
  VisualMapComponent,
  CanvasRenderer,
])
echarts.registerMap('china-university', chinaGeoJson)

const props = defineProps({
  apiBase: { type: String, required: true },
  cityOptions: { type: Array, default: () => [] },
  initialTab: { type: String, default: 'overview' },
  initialStudentPage: { type: Number, default: 1 },
})
const emit = defineEmits(['logout', 'tab-change', 'student-page-change'])

const activeTab = ref(props.initialTab)
const loading = ref(true)
const sourceNotice = ref('')
const dashboard = ref(null)
const mapElement = ref(null)
const demandChartElement = ref(null)
const regionChartElement = ref(null)
const regionExplorerElement = ref(null)
const salaryInsightChartElement = ref(null)
let mapChart = null
let demandChart = null
let regionChart = null
let regionExplorerChart = null
let salaryInsightChart = null
const filters = ref({ city: '', industry: '', education: '', category: '', companyScale: '', keyword: '' })
const selectedProvinceMetric = ref('jobCount')
const demandChartMode = ref('rank')
const regionChartMode = ref('profile')
const regionExplorerMode = ref('structure')
const salaryInsightMode = ref('salary')
const selectedProvince = ref('广东')
const selectedFamily = ref('技术研发')
const selectedJob = ref('')
const selectedIndustry = ref('')
const selectedSalaryBucket = ref('5k-8k')
const selectedSkill = ref('Python')
const selectedQualityKey = ref('experience_requirement')
let dashboardRetryCount = 0
let dashboardRetryTimer = null

const tabs = [
  { key: 'overview', label: '总览大屏' },
  { key: 'demand', label: '岗位需求' },
  { key: 'region', label: '地区行业' },
  { key: 'salary', label: '薪资技能' },
  { key: 'students', label: '学生情况' },
]

const demandChartModes = [
  { key: 'rank', label: '排行', hint: '查看热门岗位的数量排行，适合快速抓重点。' },
  { key: 'treemap', label: '矩形树', hint: '按岗位大类和细分岗位逐层展开，适合看结构。' },
  { key: 'sankey', label: '流向', hint: '展示岗位大类到技能和薪资段的关系流向。' },
  { key: 'scatter', label: '气泡', hint: '看岗位数量和薪资之间的分布关系。' },
  { key: 'heatmap', label: '热力', hint: '看岗位大类和行业之间的交叉强度。' },
  { key: 'radar', label: '雷达', hint: '从热度、薪资、门槛和技能角度综合看单个岗位。' },
]

const regionChartModes = [
  { key: 'profile', label: '画像', hint: '把当前地区的岗位、薪资和结构信息做成综合画像。' },
  { key: 'industry', label: '行业', hint: '看该地区主要岗位集中在哪些行业。' },
  { key: 'treemap', label: '树图', hint: '把地区内岗位大类和细分岗位展开成层级图。' },
  { key: 'scatter', label: '散点', hint: '对比各省岗位数与平均薪资，观察地区分层。' },
  { key: 'radar', label: '雷达', hint: '用多个维度概括当前地区的就业画像。' },
]

const regionExplorerModes = [
  { key: 'structure', label: '结构占比', hint: '放大展示重点地区的岗位大类结构，适合横向比较地区差异。' },
  { key: 'matrix', label: '行业热力', hint: '展示地区和行业的交叉需求强度，点击单元格可以联动地区和行业筛选。' },
]

const salaryInsightModes = [
  { key: 'salary', label: '薪资', hint: '查看薪资区间分布和当前筛选下的主要薪资段。' },
  { key: 'education', label: '学历', hint: '查看学历门槛分布，辅助判断岗位进入门槛。' },
  { key: 'skills', label: '技能', hint: '查看高频技能信号，作为岗位训练需求参考。' },
]

const defaultRegionProfile = {
  name: '地区',
  summary: '该地区详情以岗位样本、薪资、行业结构和高校端资源入口为主。公开统计口径未覆盖的指标，可后续接入教育厅、人社厅或学校就业系统。',
  industryFocus: ['结合岗位样本识别优势行业', '关注专业与地区产业匹配', '结合就业服务平台补充政策信息'],
  universityFocus: ['毕业生规模：建议接入省级教育/就业口径', '待就业人数：建议接入学校就业系统', '校企合作：结合代表企业和产业园区梳理'],
  companies: ['代表企业待维护'],
  universities: ['代表高校待维护'],
  links: [
    { label: '国家统计局', url: 'https://www.stats.gov.cn/' },
    { label: '教育部高校学生司', url: 'https://www.moe.gov.cn/s78/A15/' },
  ],
}

const regionProfiles = {
  广东: {
    name: '广东',
    summary: '广东就业市场与珠三角制造业、电子信息、互联网和现代服务业联系紧密，适合重点观察智能制造、软件开发、电子通信、跨境电商和金融科技等方向。',
    industryFocus: ['电子信息与软件服务', '先进制造与新能源汽车', '跨境电商与现代服务业'],
    universityFocus: ['毕业生规模需接广东教育/就业官方口径', '珠三角城市岗位密集，适合做校企合作重点区域', '可按广州、深圳、东莞、佛山拆分就业去向'],
    companies: ['华为', '腾讯', '比亚迪', '美的', '广汽集团'],
    universities: ['中山大学', '华南理工大学', '暨南大学', '深圳大学'],
    links: [
      { label: '广东省统计局', url: 'https://stats.gd.gov.cn/' },
      { label: '广东省教育厅', url: 'https://edu.gd.gov.cn/' },
      { label: '广东省人社厅', url: 'https://hrss.gd.gov.cn/' },
    ],
  },
  北京: {
    name: '北京',
    summary: '北京的岗位需求更偏总部经济、互联网、人工智能、金融科技、科研服务和公共服务，适合观察高学历岗位、算法研发和产品运营方向。',
    industryFocus: ['人工智能与软件信息服务', '金融科技与总部经济', '科研教育与公共服务'],
    universityFocus: ['高校与科研院所密集，适合研究生和高技能岗位对接', '岗位学历门槛相对较高，需关注硕士及以上需求', '可重点跟踪中关村相关产业资源'],
    companies: ['字节跳动', '百度', '京东', '小米', '联想'],
    universities: ['北京大学', '清华大学', '北京航空航天大学', '中国人民大学'],
    links: [
      { label: '北京市统计局', url: 'https://tjj.beijing.gov.cn/' },
      { label: '北京市教委', url: 'https://jw.beijing.gov.cn/' },
      { label: '北京市人社局', url: 'https://rsj.beijing.gov.cn/' },
    ],
  },
  上海: {
    name: '上海',
    summary: '上海岗位结构与金融、贸易、软件信息、集成电路、生物医药和高端服务业联系紧密，适合观察复合型岗位和高薪区间。',
    industryFocus: ['金融与专业服务', '集成电路与生物医药', '国际贸易与数字经济'],
    universityFocus: ['适合财经、计算机、医药、外语和管理类专业重点对接', '可关注临港、张江等产业资源', '毕业生去向可结合长三角流动分析'],
    companies: ['拼多多', '携程', '上汽集团', '复星医药', '上海电气'],
    universities: ['复旦大学', '上海交通大学', '同济大学', '华东师范大学'],
    links: [
      { label: '上海市统计局', url: 'https://tjj.sh.gov.cn/' },
      { label: '上海市教委', url: 'https://edu.sh.gov.cn/' },
      { label: '上海市人社局', url: 'https://rsj.sh.gov.cn/' },
    ],
  },
  浙江: {
    name: '浙江',
    summary: '浙江岗位需求与数字经济、电子商务、智能制造、平台经济和民营企业生态联系紧密，适合观察互联网运营、数据分析和制造业数字化方向。',
    industryFocus: ['数字经济与电子商务', '智能制造与产业互联网', '现代物流与消费服务'],
    universityFocus: ['杭州、宁波等城市岗位吸纳能力较强', '适合计算机、数据、经管、工业工程等专业对接', '民营企业多，可关注中小企业岗位质量'],
    companies: ['阿里巴巴', '海康威视', '吉利控股', '网易杭州', '传化智联'],
    universities: ['浙江大学', '杭州电子科技大学', '浙江工业大学', '宁波大学'],
    links: [
      { label: '浙江省统计局', url: 'https://tjj.zj.gov.cn/' },
      { label: '浙江省教育厅', url: 'https://jyt.zj.gov.cn/' },
      { label: '浙江省人社厅', url: 'https://rlsbt.zj.gov.cn/' },
    ],
  },
  江苏: {
    name: '江苏',
    summary: '江苏的就业需求与先进制造、软件服务、生物医药、集成电路和外向型经济相关，适合做长三角制造业与研发岗位观察。',
    industryFocus: ['先进制造与装备', '软件和集成电路', '生物医药与新材料'],
    universityFocus: ['苏南岗位密集，南京高校资源集中', '适合电子信息、机械、材料、生物医药等专业', '可按南京、苏州、无锡拆分校企合作资源'],
    companies: ['苏宁易购', '恒瑞医药', '徐工集团', '中车南京浦镇', '盛虹集团'],
    universities: ['南京大学', '东南大学', '南京航空航天大学', '苏州大学'],
    links: [
      { label: '江苏省统计局', url: 'https://tj.jiangsu.gov.cn/' },
      { label: '江苏省教育厅', url: 'https://jyt.jiangsu.gov.cn/' },
      { label: '江苏省人社厅', url: 'https://jshrss.jiangsu.gov.cn/' },
    ],
  },
  四川: {
    name: '四川',
    summary: '四川岗位需求以成都为核心，覆盖电子信息、软件服务、装备制造、生物医药和生活服务，适合观察西部地区人才吸纳和区域流动。',
    industryFocus: ['电子信息与软件服务', '装备制造与能源化工', '医药健康与文旅消费'],
    universityFocus: ['成都岗位集中度高，适合省内高校就业投放', '可关注成渝地区双城经济圈带来的产业协同', '适合计算机、电子、机械、医药和服务管理类专业'],
    companies: ['京东方成都', '通威集团', '新希望集团', '四川长虹', '极米科技'],
    universities: ['四川大学', '电子科技大学', '西南交通大学', '西南财经大学'],
    links: [
      { label: '四川省统计局', url: 'https://tjj.sc.gov.cn/' },
      { label: '四川省教育厅', url: 'https://edu.sc.gov.cn/' },
      { label: '四川省人社厅', url: 'https://rst.sc.gov.cn/' },
    ],
  },
  湖北: {
    name: '湖北',
    summary: '湖北以武汉为核心，高校资源密集，岗位需求覆盖光电子信息、汽车制造、生物医药、软件服务和公共服务。',
    industryFocus: ['光电子信息', '汽车与智能制造', '生物医药与软件服务'],
    universityFocus: ['高校毕业生供给较集中，适合做留鄂就业观察', '武汉光谷可作为重点产业资源入口', '适合光电、计算机、汽车、医药类专业对接'],
    companies: ['东风汽车', '烽火通信', '长江存储', '九州通', '小米武汉'],
    universities: ['武汉大学', '华中科技大学', '武汉理工大学', '华中师范大学'],
    links: [
      { label: '湖北省统计局', url: 'https://tjj.hubei.gov.cn/' },
      { label: '湖北省教育厅', url: 'https://jyt.hubei.gov.cn/' },
      { label: '湖北省人社厅', url: 'https://rst.hubei.gov.cn/' },
    ],
  },
  陕西: {
    name: '陕西',
    summary: '陕西以西安为核心，科研院所和高校资源密集，岗位需求常见于电子信息、航空航天、软件服务、能源化工和装备制造。',
    industryFocus: ['航空航天与装备制造', '电子信息与软件服务', '能源化工与科研服务'],
    universityFocus: ['西安高校密集，适合做本地留才和军工/硬科技岗位对接', '关注本科和研究生岗位分层', '适合电子、机械、材料、计算机和能源类专业'],
    companies: ['华为西安', '隆基绿能', '陕汽集团', '中兴西安', '西部超导'],
    universities: ['西安交通大学', '西北工业大学', '西安电子科技大学', '陕西师范大学'],
    links: [
      { label: '陕西省统计局', url: 'https://tjj.shaanxi.gov.cn/' },
      { label: '陕西省教育厅', url: 'https://jyt.shaanxi.gov.cn/' },
      { label: '陕西省人社厅', url: 'https://rst.shaanxi.gov.cn/' },
    ],
  },
}

const provinceNames = [
  '北京', '天津', '河北', '山西', '内蒙古', '辽宁', '吉林', '黑龙江',
  '上海', '江苏', '浙江', '安徽', '福建', '江西', '山东', '河南',
  '湖北', '湖南', '广东', '广西', '海南', '重庆', '四川', '贵州',
  '云南', '西藏', '陕西', '甘肃', '青海', '宁夏', '新疆', '香港',
  '澳门', '台湾',
]

const standardIndustries = [
  '信息技术', '教育培训', '智能制造', '电子通信', '金融财会', '建筑地产', '医药健康',
  '批发零售', '文化传媒', '交通物流', '能源化工', '农林牧渔', '公共服务', '生活服务', '其他',
]
const defaultEducations = ['不限', '专科及以上', '本科', '本科及以上', '硕士及以上', '博士']
const defaultCategories = ['软件开发', '后端开发', '前端开发', '大数据开发', '人工智能', '数据分析', '测试', '运维', '产品', '市场营销', '行政管理', '设计']
const defaultCompanyScales = ['20人以下', '20-99人', '100-499人', '500-999人', '1000-9999人', '10000人以上']

const familyDefinitions = [
  { family: '技术研发', typicalJobs: ['软件开发', '算法', '测试', '运维', '硬件工程师'], rule: '产出代码、技术方案或产品原型' },
  { family: '产品运营', typicalJobs: ['产品经理', '用户运营', '数据分析', '项目管理'], rule: '围绕产品生命周期，连接技术与市场' },
  { family: '市场销售', typicalJobs: ['销售', '商务拓展', '客户经理', '渠道管理'], rule: '直接创造收入，有明确的业绩指标' },
  { family: '职能支持', typicalJobs: ['HR', '财务', '法务', '行政', '采购'], rule: '支撑公司运转，不直接创收' },
  { family: '设计创意', typicalJobs: ['UI/UX设计', '平面设计', '视频剪辑', '文案策划'], rule: '产出视觉、内容或体验方案' },
  { family: '生产供应链', typicalJobs: ['制造', '质量', '物流', '仓储', '采购执行'], rule: '涉及实体产品的生产与流转' },
]

const familyColors = {
  技术研发: '#3156a3',
  产品运营: '#43826f',
  市场销售: '#c76f3d',
  职能支持: '#7a6aa6',
  设计创意: '#b54d6b',
  生产供应链: '#8c7a2f',
  其他: '#87949a',
}

const demoRows = [
  { jobName: '华为云数据开发工程师', companyName: '华为云计算技术有限公司', city: '深圳', province: '广东', industry: '信息技术', education: '本科及以上', category: '大数据开发', companyScale: '10000人以上', salaryMin: 12000, salaryMax: 22000, skills: ['Java', 'Spark', 'SQL', 'Python'], count: 320 },
  { jobName: '华为数字能源硬件测试工程师', companyName: '华为数字能源技术有限公司', city: '西安', province: '陕西', industry: '电子通信', education: '本科及以上', category: '测试', companyScale: '10000人以上', salaryMin: 10000, salaryMax: 18000, skills: ['测试', 'Linux', 'Python'], count: 140 },
  { jobName: '后端开发工程师', companyName: '阿里云智能集团', city: '杭州', province: '浙江', industry: '信息技术', education: '本科及以上', category: '后端开发', companyScale: '10000人以上', salaryMin: 13000, salaryMax: 24000, skills: ['Java', 'MySQL', 'Redis'], count: 280 },
  { jobName: '前端开发工程师', companyName: '腾讯科技', city: '深圳', province: '广东', industry: '信息技术', education: '本科及以上', category: '前端开发', companyScale: '10000人以上', salaryMin: 11000, salaryMax: 20000, skills: ['Vue', 'JavaScript', 'TypeScript'], count: 210 },
  { jobName: '数据分析师', companyName: '字节跳动', city: '北京', province: '北京', industry: '信息技术', education: '本科及以上', category: '数据分析', companyScale: '10000人以上', salaryMin: 12000, salaryMax: 21000, skills: ['SQL', 'Python', 'Excel'], count: 260 },
  { jobName: '教育产品运营', companyName: '新东方教育科技', city: '北京', province: '北京', industry: '教育培训', education: '本科', category: '产品', companyScale: '1000-9999人', salaryMin: 7000, salaryMax: 12000, skills: ['运营', '用户研究', 'Excel'], count: 190 },
  { jobName: '智能制造工程师', companyName: '中车时代电气', city: '成都', province: '四川', industry: '智能制造', education: '本科及以上', category: '软件开发', companyScale: '1000-9999人', salaryMin: 8500, salaryMax: 14500, skills: ['C++', '自动化', 'Linux'], count: 175 },
  { jobName: '质量工程师', companyName: '比亚迪汽车工业', city: '深圳', province: '广东', industry: '智能制造', education: '本科', category: '测试', companyScale: '10000人以上', salaryMin: 7500, salaryMax: 13000, skills: ['质量管理', 'Excel', '统计分析'], count: 180 },
  { jobName: '金融数据分析师', companyName: '平安科技', city: '上海', province: '上海', industry: '金融财会', education: '本科及以上', category: '数据分析', companyScale: '10000人以上', salaryMin: 11500, salaryMax: 19000, skills: ['SQL', 'Python', '风控'], count: 150 },
  { jobName: '物流算法运营', companyName: '京东物流', city: '北京', province: '北京', industry: '交通物流', education: '本科', category: '数据分析', companyScale: '10000人以上', salaryMin: 9000, salaryMax: 16000, skills: ['SQL', 'Python', '运营'], count: 155 },
  { jobName: '医药产品专员', companyName: '迈瑞医疗', city: '武汉', province: '湖北', industry: '医药健康', education: '本科', category: '市场营销', companyScale: '10000人以上', salaryMin: 8000, salaryMax: 13000, skills: ['沟通', '产品知识', '数据分析'], count: 110 },
  { jobName: '跨境电商运营', companyName: '希音科技', city: '广州', province: '广东', industry: '批发零售', education: '本科', category: '产品', companyScale: '10000人以上', salaryMin: 8500, salaryMax: 15000, skills: ['运营', 'Excel', '英语'], count: 125 },
  { jobName: '品牌策划', companyName: '芒果超媒', city: '长沙', province: '湖南', industry: '文化传媒', education: '本科', category: '设计', companyScale: '1000-9999人', salaryMin: 6500, salaryMax: 11000, skills: ['策划', '文案', '用户洞察'], count: 90 },
  { jobName: '新能源工艺工程师', companyName: '宁德时代', city: '宁德', province: '福建', industry: '能源化工', education: '本科及以上', category: '测试', companyScale: '10000人以上', salaryMin: 9000, salaryMax: 15000, skills: ['工艺', '质量管理', '数据分析'], count: 135 },
  { jobName: '建筑数字化顾问', companyName: '广联达科技', city: '西安', province: '陕西', industry: '建筑地产', education: '本科', category: '产品', companyScale: '1000-9999人', salaryMin: 8000, salaryMax: 13500, skills: ['产品', '项目管理', '沟通'], count: 105 },
  { jobName: '公共服务数据专员', companyName: '城市大脑研究院', city: '杭州', province: '浙江', industry: '公共服务', education: '本科及以上', category: '数据分析', companyScale: '100-499人', salaryMin: 8500, salaryMax: 14000, skills: ['SQL', '数据治理', '可视化'], count: 95 },
  { jobName: '农业物联网工程师', companyName: '极飞科技', city: '广州', province: '广东', industry: '农林牧渔', education: '本科', category: '软件开发', companyScale: '1000-9999人', salaryMin: 9000, salaryMax: 16000, skills: ['Python', '物联网', '嵌入式'], count: 80 },
  { jobName: '生活服务增长运营', companyName: '美团', city: '成都', province: '四川', industry: '生活服务', education: '本科', category: '产品', companyScale: '10000人以上', salaryMin: 8500, salaryMax: 14500, skills: ['运营', 'SQL', 'Excel'], count: 170 },
  { jobName: '半导体工艺工程师', companyName: '台积电', city: '台湾', province: '台湾', industry: '电子通信', education: '本科及以上', category: '测试', companyScale: '10000人以上', salaryMin: 11500, salaryMax: 21000, skills: ['工艺', '质量管理', '统计分析'], count: 75 },
  { jobName: '金融科技管培生', companyName: '香港交易所', city: '香港', province: '香港', industry: '金融财会', education: '本科及以上', category: '产品', companyScale: '1000-9999人', salaryMin: 13000, salaryMax: 23000, skills: ['金融', 'SQL', '英语'], count: 60 },
]

const filterGroups = {
  overview: ['keyword', 'city', 'industry', 'education'],
  demand: ['keyword', 'industry', 'education', 'category'],
  region: ['city', 'industry', 'category'],
  salary: ['city', 'industry', 'education', 'companyScale'],
}

const current = computed(() => dashboard.value || buildDemoDashboard(filters.value))
const activeFilterKeys = computed(() => filterGroups[activeTab.value] || filterGroups.overview)
const regionOptions = computed(() => unique([...provinceNames, ...props.cityOptions, ...(current.value.cities || []).map((item) => item.key)]))
const industryOptions = computed(() => unique([...standardIndustries, ...(current.value.industries || []).map((item) => item.key)]))
const educationOptions = computed(() => unique([...defaultEducations, ...(current.value.education || []).map((item) => item.key)]))
const categoryOptions = computed(() => unique([...defaultCategories, ...(current.value.jobCategories || []).map((item) => item.key)]))
const companyScaleOptions = computed(() => unique([...defaultCompanyScales, ...(current.value.companyScales || []).map((item) => item.key)]))
const maxHeatmapValue = computed(() => Math.max(1, ...(current.value.cityIndustryHeatmap || []).map((item) => item.jobCount)))
const provinceTiles = computed(() => buildProvinceTiles(current.value))
const selectedProvinceCell = computed(() => provinceTiles.value.find((item) => item.name === selectedProvince.value) || provinceTiles.value.find((item) => item.jobCount > 0) || provinceTiles.value[0])
const selectedProvinceOverview = computed(() => selectedProvinceStats())
const regionProfile = computed(() => ({
  ...defaultRegionProfile,
  ...(regionProfiles[selectedProvinceCell.value?.name] || {}),
  name: selectedProvinceCell.value?.name || defaultRegionProfile.name,
}))
const filteredFamilyMetrics = computed(() => (current.value.categoryFamilies || []).filter((item) => item.jobCount > 0))
const selectedFamilyMetric = computed(() => filteredFamilyMetrics.value.find((item) => item.family === selectedFamily.value) || filteredFamilyMetrics.value[0])
const selectedJobMetric = computed(() => (current.value.hotJobs || []).find((item) => item.key === selectedJob.value) || current.value.hotJobs?.[0])
const selectedIndustryMetric = computed(() => (current.value.industries || []).find((item) => item.key === selectedIndustry.value) || current.value.industries?.[0])
const selectedSalaryMetric = computed(() => (current.value.salaryBuckets || []).find((item) => item.key === selectedSalaryBucket.value) || current.value.salaryBuckets?.[0])
const selectedSkillMetric = computed(() => (current.value.hotSkills || []).find((item) => item.key === selectedSkill.value) || current.value.hotSkills?.[0])
const activeFilterChips = computed(() => [
  chip('关键词', filters.value.keyword),
  chip('地区', filters.value.city),
  chip('行业', filters.value.industry),
  chip('学历', filters.value.education),
  chip('岗位方向', filters.value.category),
  chip('企业规模', filters.value.companyScale),
].filter(Boolean))
const qualityScore = computed(() => {
  const items = current.value.dataQuality?.missingFields || []
  const averageMissing = items.length ? items.reduce((sum, item) => sum + Number(item.rate || 0), 0) / items.length : 0
  return Math.max(0, Math.round(100 - averageMissing))
})
const selectedQualityItem = computed(() => (current.value.dataQuality?.missingFields || []).find((item) => item.key === selectedQualityKey.value) || current.value.dataQuality?.missingFields?.[0])
const selectedProvinceRegion = computed(() => (current.value.regionalCategoryShares || []).find((item) => item.city === selectedProvinceCell.value?.name))
const selectedProvinceIndustries = computed(() => (current.value.cityIndustryHeatmap || [])
  .filter((item) => item.x === selectedProvinceCell.value?.name)
  .sort((left, right) => Number(right.jobCount || 0) - Number(left.jobCount || 0))
  .slice(0, 4))
const selectedProvinceCategories = computed(() => selectedProvinceRegion.value?.categories?.length
  ? selectedProvinceRegion.value.categories
  : filteredFamilyMetrics.value.slice(0, 4).map((item) => ({ key: item.family, jobCount: item.jobCount })))
const mapData = computed(() => {
  const byName = new Map(provinceTiles.value.map((item) => [item.name, item]))
  return chinaGeoJson.features.map((feature) => {
    const geoName = feature.properties?.name || ''
    const name = provinceDisplayName(geoName)
    const item = byName.get(name) || { name, jobCount: 0, averageSalary: 0 }
    return {
      name: geoName,
      value: provinceMetricValue(item),
      item,
    }
  })
})

const kpis = computed(() => [
  { label: '有效岗位数', value: formatNumber(current.value.summary.jobCount), icon: BriefcaseBusiness, detail: ['当前筛选条件下可参与统计的有效岗位总量。'] },
  { label: '覆盖企业', value: formatNumber(current.value.summary.companyCount), icon: Building2, detail: ['当前岗位样本覆盖的企业数量。'] },
  { label: '覆盖地区', value: formatNumber(current.value.summary.cityCount), icon: MapPinned, detail: [`主要地区：${topNames(current.value.cities, 5)}`] },
  { label: '平均月薪', value: salaryValue(current.value.summary.averageSalary), icon: ChartNoAxesCombined, detail: [`中位数：${salaryValue(current.value.summary.medianSalary)}`, `最高薪资：${salaryValue(current.value.summary.maxSalary)}`, `主要区间：${topNames(current.value.salaryBuckets, 3)}`] },
  { label: '低经验岗位占比', value: ratio(current.value.summary.entryFriendlyCount, current.value.summary.jobCount), icon: GraduationCap, detail: ['包含经验不限、应届、1 年以内或经验字段为空的岗位。'] },
  { label: '已识别技能岗位', value: formatNumber(current.value.summary.skillJobCount), icon: Sparkles, detail: ['指岗位描述中已抽取或关联到技能标签的岗位。', `高频技能：${topNames(current.value.hotSkills, 4)}`] },
])

async function loadDashboard() {
  loading.value = true
  sourceNotice.value = ''
  const params = new URLSearchParams()
  Object.entries(filters.value).forEach(([key, value]) => {
    if (String(value || '').trim()) params.set(key, String(value).trim())
  })
  try {
    const payload = await apiRequest(props.apiBase, `/university/market-dashboard?${params}`)
    if (!payload?.summary) throw new Error('高校端看板接口结构不完整')
    dashboard.value = normalizeDashboard(payload)
    sourceNotice.value = ''
    dashboardRetryCount = 0
    if (dashboardRetryTimer) {
      clearTimeout(dashboardRetryTimer)
      dashboardRetryTimer = null
    }
  } catch (cause) {
    dashboard.value = buildDemoDashboard(filters.value)
    sourceNotice.value = '实时数据暂不可用，当前展示示例数据。'
    console.warn('University dashboard fallback:', cause)
    if (!dashboardRetryTimer && dashboardRetryCount < 3) {
      dashboardRetryCount += 1
      dashboardRetryTimer = setTimeout(() => {
        dashboardRetryTimer = null
        loadDashboard()
      }, 1800)
    }
  } finally {
    loading.value = false
    syncSelections()
  }
}

function resetFilters() {
  filters.value = { city: '', industry: '', education: '', category: '', companyScale: '', keyword: '' }
  loadDashboard()
}

function showFilter(key) {
  return activeFilterKeys.value.includes(key)
}

function clearFilter(key) {
  filters.value[key] = ''
  loadDashboard()
}

function drillIntoCity(city) {
  filters.value.city = city
  loadDashboard()
}

function syncSelections() {
  selectedFamily.value = selectedFamilyMetric.value?.family || '技术研发'
  selectedJob.value = selectedJobMetric.value?.key || ''
  selectedIndustry.value = selectedIndustryMetric.value?.key || ''
  selectedSalaryBucket.value = selectedSalaryMetric.value?.key || '5k-8k'
  selectedSkill.value = selectedSkillMetric.value?.key || 'Python'
  selectedQualityKey.value = selectedQualityItem.value?.key || 'experience_requirement'
  selectedProvince.value = selectedProvinceCell.value?.name || '广东'
}

function buildDemoDashboard(filter) {
  const rows = demoRows.filter((row) => demoRowMatches(row, filter))
  const total = sum(rows, (row) => row.count)
  const averageSalary = weightedAverage(rows, (row) => (row.salaryMin + row.salaryMax) / 2)
  const medianSalary = weightedMedian(rows)
  const cityCount = unique(rows.map((row) => row.province)).length
  const skillJobCount = sum(rows.filter((row) => row.skills.length), (row) => row.count)
  const categoryFamilies = buildCategoryFamilies(rows)
  const cities = metrics(rows, (row) => row.city, 20)
  const industries = metrics(rows, (row) => row.industry, 20)
  const education = metrics(rows, (row) => row.education, 20)
  const companyScales = metrics(rows, (row) => row.companyScale, 20)
  const jobCategories = metrics(rows, (row) => row.category, 20)
  const hotJobs = metrics(rows, (row) => row.jobName, 20)
  const hotSkills = skillMetrics(rows)
  const salaryBuckets = salaryBucketMetrics(rows)
  const regionalCategoryShares = regionalShares(rows)
  const cityIndustryHeatmap = heatmap(rows)
  return {
    statDate: '2026-07-11',
    filter: { ...filter },
    summary: {
      jobCount: total,
      companyCount: unique(rows.map((row) => row.companyName)).length,
      cityCount,
      industryCount: unique(rows.map((row) => row.industry)).length,
      averageSalary,
      medianSalary,
      maxSalary: Math.max(0, ...rows.map((row) => row.salaryMax)),
      entryFriendlyCount: Math.round(total * 0.72),
      skillJobCount,
    },
    cities,
    industries,
    education,
    companyScales,
    jobCategories,
    hotJobs,
    hotSkills,
    salaryBuckets,
    categoryFamilies,
    regionalCategoryShares,
    cityIndustryHeatmap,
    provinceDemand: metrics(rows, (row) => row.province, provinceNames.length),
    suggestions: suggestionsFor(rows, categoryFamilies, cities, hotSkills),
    dataQuality: buildDemoQuality(total),
    dataBasis: '近期公开岗位，数据更新至 2026-07-11。',
  }
}

function normalizeDashboard(payload) {
  return {
    ...payload,
    provinceDemand: payload.provinceDemand || [],
    categoryFamilies: payload.categoryFamilies || [],
    regionalCategoryShares: payload.regionalCategoryShares || [],
    cityIndustryHeatmap: payload.cityIndustryHeatmap || [],
    salaryBuckets: payload.salaryBuckets || [],
    hotSkills: payload.hotSkills || [],
    hotJobs: payload.hotJobs || [],
  }
}

function demoRowMatches(row, filter) {
  const keyword = String(filter.keyword || '').trim()
  const region = String(filter.city || '').trim()
  return (!keyword || `${row.jobName}${row.companyName}${row.industry}${row.category}${row.skills.join('')}`.includes(keyword))
    && (!region || row.province === region || row.city === region)
    && (!filter.industry || row.industry === filter.industry)
    && (!filter.education || row.education === filter.education)
    && (!filter.category || row.category === filter.category)
    && (!filter.companyScale || row.companyScale === filter.companyScale)
}

function metrics(rows, keySelector, limit) {
  const grouped = new Map()
  for (const row of rows) {
    const key = keySelector(row) || '未标注'
    const item = grouped.get(key) || { key, jobCount: 0, salaryMin: 0, salaryMax: 0 }
    item.jobCount += row.count
    item.salaryMin += row.salaryMin * row.count
    item.salaryMax += row.salaryMax * row.count
    grouped.set(key, item)
  }
  return [...grouped.values()]
    .map((item) => ({ key: item.key, jobCount: item.jobCount, averageSalaryMin: Math.round(item.salaryMin / item.jobCount), averageSalaryMax: Math.round(item.salaryMax / item.jobCount) }))
    .sort((left, right) => right.jobCount - left.jobCount || left.key.localeCompare(right.key, 'zh-CN'))
    .slice(0, limit)
}

function buildCategoryFamilies(rows) {
  return familyDefinitions.map((definition) => {
    const familyRows = rows.filter((row) => categoryFamily(row.category, row.jobName) === definition.family)
    return {
      ...definition,
      jobCount: sum(familyRows, (row) => row.count),
      categories: metrics(familyRows, (row) => row.category, 6).map((item) => ({ key: item.key, jobCount: item.jobCount })),
    }
  })
}

function skillMetrics(rows) {
  const grouped = new Map()
  for (const row of rows) {
    for (const skill of row.skills) grouped.set(skill, (grouped.get(skill) || 0) + row.count)
  }
  return [...grouped.entries()]
    .map(([key, jobCount]) => ({ key, jobCount }))
    .sort((left, right) => right.jobCount - left.jobCount || left.key.localeCompare(right.key, 'zh-CN'))
    .slice(0, 30)
}

function salaryBucketMetrics(rows) {
  const buckets = ['0-3k', '3k-5k', '5k-8k', '8k-12k', '12k-20k', '20k+']
  const grouped = new Map(buckets.map((key) => [key, 0]))
  for (const row of rows) grouped.set(salaryBucket((row.salaryMin + row.salaryMax) / 2), (grouped.get(salaryBucket((row.salaryMin + row.salaryMax) / 2)) || 0) + row.count)
  return buckets.map((key) => ({ key, jobCount: grouped.get(key) || 0 }))
}

function regionalShares(rows) {
  return metrics(rows, (row) => row.province, 6).map((region) => {
    const regionRows = rows.filter((row) => row.province === region.key)
    const categories = new Map()
    for (const row of regionRows) {
      const family = categoryFamily(row.category, row.jobName)
      categories.set(family, (categories.get(family) || 0) + row.count)
    }
    return {
      city: region.key,
      jobCount: region.jobCount,
      categories: [...categories.entries()].map(([key, jobCount]) => ({ key, jobCount })).sort((left, right) => right.jobCount - left.jobCount),
    }
  })
}

function heatmap(rows) {
  const grouped = new Map()
  for (const row of rows) {
    const key = `${row.province}::${row.industry}`
    grouped.set(key, (grouped.get(key) || 0) + row.count)
  }
  return [...grouped.entries()]
    .map(([key, jobCount]) => {
      const [x, y] = key.split('::')
      return { x, y, jobCount }
    })
    .sort((left, right) => right.jobCount - left.jobCount)
    .slice(0, 36)
}

function buildProvinceTiles(payload) {
  const grouped = new Map(provinceNames.map((name) => [name, { name, jobCount: 0, salaryTotal: 0, averageSalary: 0 }]))
  const source = Array.isArray(payload.provinceDemand) && payload.provinceDemand.length
    ? payload.provinceDemand
    : (payload.cities || []).map((item) => ({ ...item, key: provinceOf(item.key) }))
  for (const item of source) {
    const province = provinceOf(item.key)
    if (!grouped.has(province)) continue
    const cell = grouped.get(province)
    const count = Number(item.jobCount || 0)
    const avgSalary = item.averageSalaryMin && item.averageSalaryMax ? (Number(item.averageSalaryMin) + Number(item.averageSalaryMax)) / 2 : 0
    cell.jobCount += count
    cell.salaryTotal += avgSalary * count
    cell.averageSalary = cell.jobCount ? Math.round(cell.salaryTotal / cell.jobCount) : 0
  }
  const values = [...grouped.values()]
  const maxValue = Math.max(1, ...values.map((item) => provinceMetricValue(item)))
  return values.map((item) => ({ ...item, intensity: provinceMetricValue(item) / maxValue }))
}

function buildDemoQuality(total) {
  const safeTotal = Math.max(total, 1)
  return {
    statDate: '2026-07-11',
    source: 'NCSS、国聘、猎聘、智联公开岗位',
    rawRecordCount: safeTotal + 25,
    cleanedRecordCount: safeTotal,
    excludedRecordCount: 25,
    duplicateJobIdCount: 0,
    missingFields: [
      { key: 'industry', count: Math.round(safeTotal * 0.012), rate: 1.2 },
      { key: 'company_scale', count: Math.round(safeTotal * 0.071), rate: 7.1 },
      { key: 'city', count: Math.round(safeTotal * 0.018), rate: 1.8 },
      { key: 'education_requirement', count: Math.round(safeTotal * 0.026), rate: 2.6 },
      { key: 'experience_requirement', count: Math.round(safeTotal * 0.42), rate: 42 },
      { key: 'job_description', count: Math.round(safeTotal * 0.033), rate: 3.3 },
    ],
    exclusionReasons: [
      { key: 'hard_experience_requirement', count: 22, rate: 0.18 },
      { key: 'social_recruitment_without_student_hint', count: 3, rate: 0.02 },
    ],
    salaryParseStatus: [
      { key: '已解析', count: safeTotal, rate: 100 },
      { key: '未解析', count: 0, rate: 0 },
    ],
    note: '字段质量用于说明当前岗位样本可解释性，不代表学生培养质量。',
  }
}

function suggestionsFor(rows, categoryFamilies, cities, hotSkills) {
  if (!rows.length) return ['当前筛选条件下没有岗位样本，请放宽地区、行业或学历条件。']
  return [
    `岗位需求集中在 ${cities.slice(0, 3).map((item) => item.key).join('、')}，建议作为就业信息推送和校企合作重点。`,
    `当前需求较高的大类为 ${categoryFamilies.filter((item) => item.jobCount > 0).slice(0, 2).map((item) => item.family).join('、')}，可组织分专业岗位方向宣讲。`,
    `高频技能包含 ${hotSkills.slice(0, 3).map((item) => item.key).join('、')}，适合纳入短期实训或项目制训练主题。`,
  ]
}

function categoryFamily(category, jobName) {
  const text = `${category || ''}${jobName || ''}`
  if (['软件开发', '后端开发', '前端开发', '大数据开发', '人工智能', '测试', '运维'].includes(category)
    || containsAny(text, ['软件', '算法', '测试', '运维', '硬件', '开发', '工程师', 'Java', '前端', '后端', '大数据', '人工智能'])) return '技术研发'
  if (['产品', '数据分析'].includes(category) || containsAny(text, ['产品', '运营', '数据分析', '项目管理', '用户运营'])) return '产品运营'
  if (category === '市场营销' || containsAny(text, ['销售', '市场', '商务', '客户经理', '渠道'])) return '市场销售'
  if (category === '行政管理' || containsAny(text, ['HR', '人力', '财务', '法务', '行政', '采购', '会计', '审计'])) return '职能支持'
  if (category === '设计' || containsAny(text, ['设计', 'UI', 'UX', '视频', '剪辑', '文案', '策划'])) return '设计创意'
  if (containsAny(text, ['制造', '质量', '物流', '仓储', '供应链', '机械', '电气', '自动化', '生产', '工艺'])) return '生产供应链'
  return '其他'
}

function containsAny(value, keywords) {
  return keywords.some((keyword) => String(value || '').includes(keyword))
}

function provinceOf(value) {
  const name = String(value || '').replace(/市+$/, '').trim()
  if (provinceNames.includes(name)) return name
  return name
}

function provinceMetricValue(item) {
  return selectedProvinceMetric.value === 'salary' ? Number(item.averageSalary || 0) : Number(item.jobCount || 0)
}

function provinceTileStyle(item) {
  const alpha = item.jobCount ? 0.13 + item.intensity * 0.75 : 0.04
  return {
    background: `rgba(67, 130, 111, ${alpha})`,
    color: item.intensity > 0.55 ? '#fff' : '#173e50',
  }
}

function donutStyle(items, key = 'jobCount', label = 'family') {
  const total = (items || []).reduce((sumValue, item) => sumValue + Number(item[key] || 0), 0)
  if (!total) return { background: '#e2e8e8' }
  let start = 0
  const parts = items.map((item, index) => {
    const color = familyColors[item[label]] || familyColors[item.key] || ['#3156a3', '#43826f', '#c76f3d', '#7a6aa6', '#8c7a2f', '#b54d6b'][index % 6]
    const end = start + Number(item[key] || 0) / total * 360
    const segment = `${color} ${start}deg ${end}deg`
    start = end
    return segment
  })
  return { background: `conic-gradient(${parts.join(', ')})` }
}

function pieStyle(categories) {
  return donutStyle(categories || [], 'jobCount', 'key')
}

function heatStyle(value) {
  const strength = Number(value || 0) / maxHeatmapValue.value
  return { background: `rgba(49, 86, 163, ${0.08 + strength * 0.82})`, color: strength > 0.5 ? '#fff' : '#173e50' }
}

function renderChinaMap() {
  if (!mapElement.value) return
  if (mapChart && mapChart.getDom() !== mapElement.value) {
    mapChart.dispose()
    mapChart = null
  }
  if (!mapChart) {
    mapChart = echarts.init(mapElement.value)
    mapChart.on('click', (params) => {
      selectedProvince.value = provinceDisplayName(params.name)
    })
  }
  const values = mapData.value.map((item) => Number(item.value || 0))
  const maxValue = Math.max(1, ...values)
  mapChart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      borderWidth: 0,
      padding: 0,
      extraCssText: 'box-shadow: 0 12px 30px rgba(14, 47, 62, .18);',
      formatter: (params) => mapTooltip(params.data?.item || { name: provinceDisplayName(params.name), jobCount: 0, averageSalary: 0 }),
    },
    visualMap: {
      min: 0,
      max: maxValue,
      show: false,
      inRange: { color: ['#eef5f2', '#bdd8cd', '#6fae97', '#2f745f'] },
    },
    series: [{
      type: 'map',
      map: 'china-university',
      roam: false,
      selectedMode: false,
      data: mapData.value,
      nameProperty: 'name',
      layoutCenter: ['50%', '59%'],
      layoutSize: '116%',
      label: { show: false },
      emphasis: {
        label: { show: true, color: '#173e50', fontSize: 11, fontWeight: 700 },
        itemStyle: { areaColor: '#c7ec74', borderColor: '#173e50', borderWidth: 1.2 },
      },
      itemStyle: { borderColor: '#ffffff', borderWidth: 1, areaColor: '#edf4f1' },
    }],
  })
}

function mapTooltip(item) {
  const industries = (current.value.cityIndustryHeatmap || [])
    .filter((entry) => entry.x === item.name)
    .sort((left, right) => Number(right.jobCount || 0) - Number(left.jobCount || 0))
    .slice(0, 3)
  const categories = (current.value.regionalCategoryShares || [])
    .find((entry) => entry.city === item.name)?.categories?.slice(0, 3) || []
  return `
    <div class="map-tooltip">
      <strong>${item.name}</strong>
      <span>${formatNumber(item.jobCount)} 个岗位 · 平均 ${salaryValue(item.averageSalary)}</span>
      <p>热门行业：${industries.length ? industries.map((entry) => entry.y).join('、') : '暂无'}</p>
      <p>岗位结构：${categories.length ? categories.map((entry) => `${entry.key} ${ratio(entry.jobCount, item.jobCount)}`).join(' / ') : '暂无'}</p>
    </div>
  `
}

function categoryTooltip(item) {
  const familyName = item.family || item.key
  const family = (current.value.categoryFamilies || []).find((entry) => entry.family === familyName)
    || familyDefinitions.find((entry) => entry.family === familyName)
  const jobCount = item.jobCount ?? family?.jobCount ?? 0
  return {
    title: familyName || '暂无大类',
    typicalJobs: family?.typicalJobs?.length ? family.typicalJobs.join('、') : '暂无典型岗位',
    rule: family?.rule || '暂无归并规则',
    jobCount,
  }
}

function renderDemandChart() {
  if (!demandChartElement.value || activeTab.value !== 'demand') return
  if (demandChart && demandChart.getDom() !== demandChartElement.value) {
    demandChart.dispose()
    demandChart = null
  }
  if (!demandChart) {
    demandChart = echarts.init(demandChartElement.value)
    demandChart.on('click', (params) => {
      const name = params.data?.jobName || params.data?.name || params.name
      if ((current.value.hotJobs || []).some((item) => item.key === name)) selectedJob.value = name
      if ((current.value.categoryFamilies || []).some((item) => item.family === name)) selectedFamily.value = name
    })
  }
  demandChart.setOption(demandChartOption(), true)
}

function renderRegionChart() {
  if (!regionChartElement.value || activeTab.value !== 'region') return
  if (regionChart && regionChart.getDom() !== regionChartElement.value) {
    regionChart.dispose()
    regionChart = null
  }
  if (!regionChart) {
    regionChart = echarts.init(regionChartElement.value)
    regionChart.on('click', (params) => {
      const name = params.data?.name || params.name
      if (name && provinceNames.includes(name)) selectedProvince.value = name
    })
  }
  regionChart.setOption(regionChartOption(), true)
}

function renderRegionExplorerChart() {
  if (!regionExplorerElement.value || activeTab.value !== 'region') return
  if (regionExplorerChart && regionExplorerChart.getDom() !== regionExplorerElement.value) {
    regionExplorerChart.dispose()
    regionExplorerChart = null
  }
  if (!regionExplorerChart) {
    regionExplorerChart = echarts.init(regionExplorerElement.value)
    regionExplorerChart.on('click', (params) => {
      const name = params.data?.name || params.name
      if (name && provinceNames.includes(name)) selectedProvince.value = name
      if (params.seriesType === 'heatmap' && params.data) {
        const [province, industry] = params.data.value || []
        if (province) selectedProvince.value = province
        if (industry) selectedIndustry.value = industry
      }
    })
  }
  regionExplorerChart.setOption(regionExplorerChartOption(), true)
}

function renderSalaryInsightChart() {
  if (!salaryInsightChartElement.value || activeTab.value !== 'salary') return
  if (salaryInsightChart && salaryInsightChart.getDom() !== salaryInsightChartElement.value) {
    salaryInsightChart.dispose()
    salaryInsightChart = null
  }
  if (!salaryInsightChart) {
    salaryInsightChart = echarts.init(salaryInsightChartElement.value)
    salaryInsightChart.on('click', (params) => {
      const name = params.data?.name || params.name
      if (salaryInsightMode.value === 'salary' && name) selectedSalaryBucket.value = name
      if (salaryInsightMode.value === 'skills' && name) selectedSkill.value = name
      if (salaryInsightMode.value === 'education' && name) filters.value.education = name
    })
  }
  salaryInsightChart.setOption(salaryInsightChartOption(), true)
}

function salaryInsightChartOption() {
  if (salaryInsightMode.value === 'education') return salaryEducationOption()
  if (salaryInsightMode.value === 'skills') return salarySkillsOption()
  return salaryBucketOption()
}

function salaryBaseOption() {
  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'item', borderWidth: 0, backgroundColor: '#ffffff', textStyle: { color: '#31515d', fontSize: 12 }, extraCssText: 'box-shadow: 0 12px 30px rgba(14, 47, 62, .16);' },
    color: ['#3156a3', '#43826f', '#c76f3d', '#7a6aa6', '#b54d6b', '#8c7a2f'],
  }
}

function salaryBucketOption() {
  const items = (current.value.salaryBuckets || [])
  return {
    ...salaryBaseOption(),
    grid: { left: 42, right: 28, top: 24, bottom: 42, containLabel: true },
    xAxis: { type: 'category', data: items.map((item) => item.key), axisLabel: { color: '#31515d' } },
    yAxis: { type: 'value', axisLabel: { color: '#6f827e' }, splitLine: { lineStyle: { color: '#edf3f1' } } },
    series: [{
      type: 'bar',
      data: items.map((item) => ({ name: item.key, value: item.jobCount, itemStyle: { color: selectedSalaryMetric.value?.key === item.key ? '#173e50' : '#43826f' } })),
      barWidth: 28,
      label: { show: true, position: 'top', color: '#31515d', fontSize: 11 },
    }],
  }
}

function salaryEducationOption() {
  const items = (current.value.education || []).slice(0, 10).reverse()
  return {
    ...salaryBaseOption(),
    grid: { left: 120, right: 28, top: 22, bottom: 28, containLabel: true },
    xAxis: { type: 'value', axisLabel: { color: '#6f827e' }, splitLine: { lineStyle: { color: '#edf3f1' } } },
    yAxis: { type: 'category', data: items.map((item) => item.key), axisLabel: { color: '#31515d', width: 110, overflow: 'truncate' } },
    series: [{
      type: 'bar',
      data: items.map((item) => ({ name: item.key, value: item.jobCount, itemStyle: { color: filters.value.education === item.key ? '#173e50' : '#3156a3' } })),
      barWidth: 16,
      label: { show: true, position: 'right', formatter: ({ value }) => formatNumber(value), color: '#31515d', fontSize: 11 },
    }],
  }
}

function salarySkillsOption() {
  const data = (current.value.hotSkills || []).slice(0, 18).map((item) => ({
    name: item.key,
    value: Number(item.jobCount || 0),
    itemStyle: { color: selectedSkillMetric.value?.key === item.key ? '#173e50' : undefined },
  }))
  return {
    ...salaryBaseOption(),
    series: [{
      type: 'treemap',
      roam: false,
      nodeClick: false,
      breadcrumb: { show: false },
      top: 8,
      left: 8,
      right: 8,
      bottom: 8,
      data,
      label: { color: '#fff', fontSize: 12, formatter: '{b}' },
      itemStyle: { borderColor: '#fff', borderWidth: 2 },
    }],
  }
}

function regionExplorerChartOption() {
  if (regionExplorerMode.value === 'matrix') return regionExplorerHeatmapOption()
  return regionExplorerStackedOption()
}

function regionExplorerStackedOption() {
  const regions = (current.value.regionalCategoryShares || []).slice(0, 16)
  const categories = unique((regions || []).flatMap((region) => (region.categories || []).map((item) => item.key))).slice(0, 8)
  return {
    ...regionBaseOption(),
    grid: { left: 44, right: 20, top: 44, bottom: 72, containLabel: true },
    legend: { data: categories, top: 0, textStyle: { color: '#5d7470' } },
    tooltip: { ...regionBaseOption().tooltip, trigger: 'axis', axisPointer: { type: 'shadow' } },
    xAxis: {
      type: 'category',
      data: regions.map((item) => item.city),
      axisLabel: { color: '#31515d', rotate: 18 },
    },
    yAxis: { type: 'value', axisLabel: { color: '#6f827e' }, splitLine: { lineStyle: { color: '#edf3f1' } } },
    dataZoom: [
      { type: 'slider', height: 12, bottom: 18, brushSelect: false, borderColor: '#d8e3df', fillerColor: 'rgba(67,130,111,.18)', textStyle: { color: '#6f827e', fontSize: 10 } },
      { type: 'inside' },
    ],
    series: categories.map((category, index) => ({
      name: category,
      type: 'bar',
      stack: 'region',
      emphasis: { focus: 'series' },
      data: regions.map((region) => Number((region.categories || []).find((item) => item.key === category)?.jobCount || 0)),
      itemStyle: { color: ['#3156a3', '#43826f', '#c76f3d', '#7a6aa6', '#b54d6b', '#8c7a2f'][index % 6] },
    })),
  }
}

function regionExplorerHeatmapOption() {
  const provinces = unique((current.value.cityIndustryHeatmap || []).map((item) => item.x)).slice(0, 16)
  const industries = unique((current.value.cityIndustryHeatmap || []).map((item) => item.y)).slice(0, 12)
  const values = (current.value.cityIndustryHeatmap || [])
    .filter((item) => provinces.includes(item.x) && industries.includes(item.y))
    .map((item) => [provinces.indexOf(item.x), industries.indexOf(item.y), item.jobCount, item.x, item.y])
  return {
    ...regionBaseOption(),
    grid: { left: 104, right: 24, top: 22, bottom: 42, containLabel: true },
    tooltip: {
      ...regionBaseOption().tooltip,
      formatter: (params) => `${params.data[3]} · ${params.data[4]}<br/>岗位数：${formatNumber(params.data[2])}`,
    },
    xAxis: { type: 'category', data: provinces, axisLabel: { color: '#31515d' } },
    yAxis: { type: 'category', data: industries, axisLabel: { color: '#31515d' } },
    visualMap: {
      min: 0,
      max: Math.max(1, ...values.map((item) => item[2] || 0)),
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: 0,
      textStyle: { color: '#5d7470' },
      inRange: { color: ['#eef6f2', '#a8cfbf', '#43826f', '#173e50'] },
    },
    series: [{
      type: 'heatmap',
      data: values,
      emphasis: { itemStyle: { shadowBlur: 8, shadowColor: 'rgba(0,0,0,.16)' } },
      label: { show: false },
    }],
  }
}

function regionChartOption() {
  const mode = regionChartMode.value
  if (mode === 'industry') return regionIndustryOption()
  if (mode === 'treemap') return regionTreemapOption()
  if (mode === 'scatter') return regionScatterOption()
  if (mode === 'radar') return regionRadarOption()
  return regionProfileOption()
}

function regionBaseOption() {
  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'item', borderWidth: 0, backgroundColor: '#ffffff', textStyle: { color: '#31515d', fontSize: 12 }, extraCssText: 'box-shadow: 0 12px 30px rgba(14, 47, 62, .16);' },
    color: ['#3156a3', '#43826f', '#c76f3d', '#7a6aa6', '#b54d6b', '#8c7a2f'],
  }
}

function selectedProvinceStats() {
  const industries = selectedProvinceIndustries.value || []
  const categories = selectedProvinceCategories.value || []
  return {
    jobCount: Number(selectedProvinceCell.value?.jobCount || 0),
    averageSalary: Number(selectedProvinceCell.value?.averageSalary || 0),
    industryCount: industries.length,
    categoryCount: categories.length,
  }
}

function regionRadarMetrics() {
  const stats = selectedProvinceStats()
  const maxAverageSalary = Math.max(1, ...provinceTiles.value.map((item) => Number(item.averageSalary || 0)))
  const topCategoryCount = Math.max(0, ...selectedProvinceCategories.value.map((item) => Number(item.jobCount || 0)))
  const industryUniverse = new Set((current.value.cityIndustryHeatmap || []).map((item) => item.y)).size
  const percent = (value, maximum) => Math.min(100, Math.round(Number(value || 0) / Math.max(1, Number(maximum || 0)) * 100))
  const categoryTotal = selectedProvinceCategories.value.reduce((sum, item) => sum + Number(item.jobCount || 0), 0)
  const categoryEntropy = selectedProvinceCategories.value.reduce((sum, item) => {
    const share = Number(item.jobCount || 0) / Math.max(1, categoryTotal)
    return share ? sum - share * Math.log(share) : sum
  }, 0)
  const categoryBalance = selectedProvinceCategories.value.length > 1
    ? Math.round(categoryEntropy / Math.log(selectedProvinceCategories.value.length) * 100)
    : 0
  return {
    stats,
    values: [
      percent(stats.jobCount, maxCount(provinceTiles.value)),
      percent(stats.averageSalary, maxAverageSalary),
      percent(stats.industryCount, industryUniverse),
      categoryBalance,
      percent(topCategoryCount, stats.jobCount),
    ],
  }
}

function regionRadarTooltip(stats, values) {
  return `${selectedProvinceCell.value?.name || '暂无地区'}<br/>岗位规模：${values[0]}%（${formatNumber(stats.jobCount)} 个岗位）<br/>薪资水平：${values[1]}%（${salaryValue(stats.averageSalary)}）<br/>行业覆盖：${values[2]}%（${stats.industryCount} 类）<br/>大类均衡度：${values[3]}%（${stats.categoryCount} 类）<br/>主导大类占比：${values[4]}%`
}

function regionProfileOption() {
  const { stats, values } = regionRadarMetrics()
  return {
    ...regionBaseOption(),
    tooltip: { ...regionBaseOption().tooltip, formatter: () => regionRadarTooltip(stats, values) },
    radar: {
      center: ['50%', '55%'],
      radius: '72%',
      indicator: [
        { name: '岗位规模', max: 100 },
        { name: '薪资水平', max: 100 },
        { name: '行业覆盖', max: 100 },
        { name: '大类均衡度', max: 100 },
        { name: '主导大类占比', max: 100 },
      ],
      axisName: { color: '#31515d', fontSize: 11 },
      splitLine: { lineStyle: { color: '#dfe8e5' } },
      splitArea: { areaStyle: { color: ['#fbfdfc', '#f2f7f5'] } },
    },
    series: [{
      type: 'radar',
      data: [{
        name: selectedProvinceCell.value?.name || '暂无地区',
        value: values,
        areaStyle: { color: 'rgba(67,130,111,.22)' },
        lineStyle: { color: '#43826f', width: 2 },
      }],
    }],
  }
}

function regionIndustryOption() {
  const items = selectedProvinceIndustries.value.slice(0, 8).reverse()
  return {
    ...regionBaseOption(),
    grid: { left: 110, right: 30, top: 18, bottom: 24 },
    xAxis: { type: 'value', splitLine: { lineStyle: { color: '#edf3f1' } }, axisLabel: { color: '#6f827e' } },
    yAxis: { type: 'category', data: items.map((item) => item.y), axisLabel: { color: '#31515d', width: 100, overflow: 'truncate' } },
    series: [{ type: 'bar', data: items.map((item) => ({ value: item.jobCount, name: item.y, itemStyle: { color: '#43826f' } })), barWidth: 14, label: { show: true, position: 'right', formatter: ({ value }) => formatNumber(value), color: '#31515d', fontSize: 11 } }],
  }
}

function regionTreemapOption() {
  const children = selectedProvinceCategories.value.map((item) => ({ name: item.key, value: Number(item.jobCount || 0) }))
  return {
    ...regionBaseOption(),
    series: [{
      type: 'treemap',
      roam: false,
      nodeClick: false,
      breadcrumb: { show: false },
      top: 6,
      left: 6,
      right: 6,
      bottom: 6,
      data: [{
        name: selectedProvinceCell.value?.name || '地区',
        value: Math.max(1, Number(selectedProvinceCell.value?.jobCount || 1)),
        children,
      }],
      label: { color: '#fff', fontSize: 12, formatter: '{b}' },
      upperLabel: { show: true, height: 24, color: '#fff', fontWeight: 800 },
      itemStyle: { borderColor: '#fff', borderWidth: 2 },
    }],
  }
}

function regionScatterOption() {
  const data = provinceTiles.value.map((item) => ({
    name: item.name,
    value: [Number(item.jobCount || 0), Number(item.averageSalary || 0), Number(item.jobCount || 0)],
    symbolSize: Math.max(12, Math.min(48, 8 + Number(item.jobCount || 0) / Math.max(1, maxCount(provinceTiles.value)) * 40)),
  }))
  return {
    ...regionBaseOption(),
    grid: { left: 58, right: 30, top: 26, bottom: 42 },
    xAxis: { name: '岗位数', type: 'value', axisLabel: { color: '#6f827e' }, splitLine: { lineStyle: { color: '#edf3f1' } } },
    yAxis: { name: '平均薪资', type: 'value', axisLabel: { formatter: (value) => salaryValue(value), color: '#6f827e' }, splitLine: { lineStyle: { color: '#edf3f1' } } },
    tooltip: { ...regionBaseOption().tooltip, formatter: (params) => `${params.name}<br/>岗位数：${formatNumber(params.value[0])}<br/>平均薪资：${salaryValue(params.value[1])}` },
    series: [{ type: 'scatter', data, itemStyle: { color: '#c76f3d', opacity: 0.76 } }],
  }
}

function regionRadarOption() {
  const { stats, values } = regionRadarMetrics()
  return {
    ...regionBaseOption(),
    tooltip: { ...regionBaseOption().tooltip, formatter: () => regionRadarTooltip(stats, values) },
    radar: {
      center: ['50%', '55%'],
      radius: '70%',
      indicator: [
        { name: '岗位规模', max: 100 },
        { name: '薪资水平', max: 100 },
        { name: '行业覆盖', max: 100 },
        { name: '大类均衡度', max: 100 },
        { name: '主导大类占比', max: 100 },
      ],
      axisName: { color: '#31515d', fontSize: 11 },
      splitLine: { lineStyle: { color: '#dfe8e5' } },
      splitArea: { areaStyle: { color: ['#fbfdfc', '#f2f7f5'] } },
    },
    series: [{
      type: 'radar',
      data: [{
        name: selectedProvinceCell.value?.name || '暂无地区',
        value: values,
        areaStyle: { color: 'rgba(49,86,163,.20)' },
        lineStyle: { color: '#3156a3', width: 2 },
      }],
    }],
  }
}

function demandChartOption() {
  const mode = demandChartMode.value
  if (mode === 'treemap') return demandTreemapOption()
  if (mode === 'sankey') return demandSankeyOption()
  if (mode === 'scatter') return demandScatterOption()
  if (mode === 'heatmap') return demandHeatmapOption()
  if (mode === 'radar') return demandRadarOption()
  return demandRankOption()
}

function demandBaseOption() {
  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'item', borderWidth: 0, backgroundColor: '#ffffff', textStyle: { color: '#31515d', fontSize: 12 }, extraCssText: 'box-shadow: 0 12px 30px rgba(14, 47, 62, .16);' },
    color: ['#3156a3', '#43826f', '#c76f3d', '#7a6aa6', '#b54d6b', '#8c7a2f'],
  }
}

function demandRankOption() {
  const jobs = (current.value.hotJobs || []).slice(0, 12).reverse()
  return {
    ...demandBaseOption(),
    grid: { left: 120, right: 28, top: 18, bottom: 24 },
    xAxis: { type: 'value', splitLine: { lineStyle: { color: '#edf3f1' } }, axisLabel: { color: '#6f827e' } },
    yAxis: { type: 'category', data: jobs.map((item) => item.key), axisLabel: { color: '#31515d', width: 108, overflow: 'truncate' } },
    series: [{
      type: 'bar',
      data: jobs.map((item) => ({ value: item.jobCount, name: item.key, jobName: item.key, itemStyle: { color: selectedJobMetric.value?.key === item.key ? '#0b2f50' : '#43826f' } })),
      barWidth: 14,
      label: { show: true, position: 'right', formatter: ({ value }) => formatNumber(value), color: '#31515d', fontSize: 11 },
    }],
  }
}

function demandTreemapOption() {
  const data = (current.value.categoryFamilies || []).map((family) => ({
    name: family.family,
    value: Number(family.jobCount || 0),
    itemStyle: { color: familyColors[family.family] || '#87949a' },
    children: (family.categories || []).map((item) => ({ name: item.key, value: Number(item.jobCount || 0) })),
  }))
  return {
    ...demandBaseOption(),
    series: [{
      type: 'treemap',
      roam: false,
      nodeClick: false,
      breadcrumb: { show: false },
      top: 8,
      left: 8,
      right: 8,
      bottom: 8,
      data,
      label: { color: '#fff', fontSize: 12, formatter: '{b}' },
      upperLabel: { show: true, height: 24, color: '#fff', fontWeight: 800 },
      itemStyle: { borderColor: '#fff', borderWidth: 2 },
    }],
  }
}

function demandSankeyOption() {
  const nodes = new Set()
  const links = []
  for (const family of current.value.categoryFamilies || []) {
    if (!Number(family.jobCount || 0)) continue
    nodes.add(family.family)
    for (const category of (family.categories || []).slice(0, 4)) {
      nodes.add(category.key)
      links.push({ source: family.family, target: category.key, value: Number(category.jobCount || 0) })
    }
  }
  const salaryTarget = selectedSalaryMetric.value?.key || '主要薪资段'
  nodes.add(salaryTarget)
  for (const job of (current.value.hotJobs || []).slice(0, 8)) {
    nodes.add(job.key)
    links.push({ source: job.key, target: salaryTarget, value: Math.max(1, Math.round(Number(job.jobCount || 0) / 4)) })
  }
  return {
    ...demandBaseOption(),
    series: [{
      type: 'sankey',
      top: 12,
      left: 8,
      right: 18,
      bottom: 12,
      nodeAlign: 'justify',
      data: [...nodes].map((name) => ({ name })),
      links,
      lineStyle: { color: 'gradient', opacity: 0.28, curveness: 0.5 },
      label: { color: '#31515d', fontSize: 11 },
      emphasis: { focus: 'adjacency' },
    }],
  }
}

function demandScatterOption() {
  const jobs = (current.value.hotJobs || []).slice(0, 18)
  const data = jobs.map((item, index) => {
    const salary = Number(item.averageSalaryMax || current.value.summary.averageSalary || 0)
    return {
      name: item.key,
      jobName: item.key,
      value: [salary, Number(item.jobCount || 0), index],
      symbolSize: Math.max(14, Math.min(54, 12 + Number(item.jobCount || 0) / Math.max(1, maxCount(jobs)) * 44)),
    }
  })
  return {
    ...demandBaseOption(),
    grid: { left: 58, right: 30, top: 26, bottom: 42 },
    xAxis: { name: '薪资', type: 'value', axisLabel: { formatter: (value) => salaryValue(value), color: '#6f827e' }, splitLine: { lineStyle: { color: '#edf3f1' } } },
    yAxis: { name: '岗位数', type: 'value', axisLabel: { color: '#6f827e' }, splitLine: { lineStyle: { color: '#edf3f1' } } },
    tooltip: { ...demandBaseOption().tooltip, formatter: (params) => `${params.name}<br/>岗位数：${formatNumber(params.value[1])}<br/>薪资参考：${salaryValue(params.value[0])}` },
    series: [{ type: 'scatter', data, itemStyle: { color: '#43826f', opacity: 0.78 }, emphasis: { itemStyle: { color: '#0b2f50', opacity: 1 } } }],
  }
}

function demandHeatmapOption() {
  const rows = (current.value.categoryFamilies || []).filter((item) => Number(item.jobCount || 0)).slice(0, 6)
  const columns = (current.value.industries || []).slice(0, 6)
  const data = []
  rows.forEach((family, rowIndex) => {
    columns.forEach((industry, columnIndex) => {
      const value = Math.round(Number(family.jobCount || 0) * Number(industry.jobCount || 0) / Math.max(1, current.value.summary.jobCount) / 3)
      data.push([columnIndex, rowIndex, value])
    })
  })
  return {
    ...demandBaseOption(),
    grid: { left: 88, right: 24, top: 28, bottom: 68 },
    xAxis: { type: 'category', data: columns.map((item) => item.key), axisLabel: { color: '#6f827e', rotate: 24 } },
    yAxis: { type: 'category', data: rows.map((item) => item.family), axisLabel: { color: '#31515d' } },
    visualMap: { show: false, min: 0, max: Math.max(1, ...data.map((item) => item[2])), inRange: { color: ['#eef5f2', '#bcd9cf', '#43826f', '#0b2f50'] } },
    series: [{ type: 'heatmap', data, label: { show: true, color: '#173e50', fontSize: 10 }, emphasis: { itemStyle: { borderColor: '#173e50', borderWidth: 1 } } }],
  }
}

function demandRadarOption() {
  const job = selectedJobMetric.value || current.value.hotJobs?.[0] || {}
  const maxJob = maxCount(current.value.hotJobs || [])
  const salary = Number(job.averageSalaryMax || current.value.summary.averageSalary || 0)
  const maxSalary = Math.max(1, Number(current.value.summary.maxSalary || salary || 1))
  const values = [
    Math.round(Number(job.jobCount || 0) / maxJob * 100),
    Math.round(salary / maxSalary * 100),
    Math.min(100, 38 + (selectedFamilyMetric.value?.categories?.length || 1) * 9),
    Math.min(100, 45 + (current.value.education?.length || 1) * 6),
    Math.round(Number(current.value.summary.entryFriendlyCount || 0) / Math.max(1, Number(current.value.summary.jobCount || 0)) * 100),
  ]
  return {
    ...demandBaseOption(),
    radar: {
      center: ['50%', '53%'],
      radius: '68%',
      indicator: [
        { name: '需求热度', max: 100 },
        { name: '薪资水平', max: 100 },
        { name: '技能复杂度', max: 100 },
        { name: '学历门槛', max: 100 },
        { name: '低经验友好', max: 100 },
      ],
      axisName: { color: '#31515d', fontSize: 11 },
      splitLine: { lineStyle: { color: '#dfe8e5' } },
      splitArea: { areaStyle: { color: ['#fbfdfc', '#f2f7f5'] } },
    },
    series: [{ type: 'radar', data: [{ name: job.key || '暂无岗位', value: values, areaStyle: { color: 'rgba(67,130,111,.22)' }, lineStyle: { color: '#43826f', width: 2 } }] }],
  }
}

function resizeChinaMap() {
  mapChart?.resize()
}

function resizeDemandChart() {
  demandChart?.resize()
}

function resizeRegionChart() {
  regionChart?.resize()
}

function resizeRegionExplorerChart() {
  regionExplorerChart?.resize()
}

function resizeSalaryInsightChart() {
  salaryInsightChart?.resize()
}

function sum(items, selector) {
  return items.reduce((total, item) => total + Number(selector(item) || 0), 0)
}

function weightedAverage(rows, selector) {
  const total = sum(rows, (row) => row.count)
  if (!total) return null
  return Math.round(sum(rows, (row) => selector(row) * row.count) / total)
}

function weightedMedian(rows) {
  const expanded = rows.flatMap((row) => Array(Math.max(1, Math.round(row.count / 20))).fill((row.salaryMin + row.salaryMax) / 2)).sort((a, b) => a - b)
  return expanded.length ? Math.round(expanded[Math.floor(expanded.length / 2)]) : null
}

function salaryBucket(value) {
  if (value < 3000) return '0-3k'
  if (value < 5000) return '3k-5k'
  if (value < 8000) return '5k-8k'
  if (value < 12000) return '8k-12k'
  if (value < 20000) return '12k-20k'
  return '20k+'
}

function topNames(items, limit) {
  const names = (items || []).filter((item) => Number(item.jobCount || 0) > 0).slice(0, limit).map((item) => item.key)
  if (!names.length) return '暂无'
  return `${names.join('、')}${(items || []).length > limit ? '…' : ''}`
}

function provinceDisplayName(value) {
  return String(value || '')
    .replace(/特别行政区$/, '')
    .replace(/维吾尔自治区$/, '')
    .replace(/壮族自治区$/, '')
    .replace(/回族自治区$/, '')
    .replace(/自治区$/, '')
    .replace(/省$/, '')
    .replace(/市$/, '')
}

function unique(items) {
  return [...new Set(items.map((item) => String(item || '').trim()).filter(Boolean))]
}

function chip(label, value) {
  return String(value || '').trim() ? { label, value: String(value).trim() } : null
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString()
}

function salaryValue(value) {
  return value ? `${Math.round(Number(value) / 1000)}K` : '暂无'
}

function salaryRange(item) {
  if (!item?.averageSalaryMin || !item?.averageSalaryMax) return '暂无'
  return `${Math.round(item.averageSalaryMin / 1000)}K-${Math.round(item.averageSalaryMax / 1000)}K`
}

function ratio(part, total) {
  if (!total) return '0%'
  return `${Math.round(Number(part || 0) / Number(total) * 100)}%`
}

function maxCount(items) {
  return Math.max(1, ...(items || []).map((item) => Number(item.jobCount || 0)))
}

function widthFor(value, items) {
  return `${Math.max(4, Math.round(Number(value || 0) / maxCount(items) * 100))}%`
}

watch([mapData, selectedProvinceMetric], () => nextTick(renderChinaMap), { deep: true })
watch([current, demandChartMode, selectedJobMetric, selectedFamilyMetric], () => nextTick(renderDemandChart), { deep: true })
watch([current, regionChartMode, selectedProvince], () => nextTick(renderRegionChart), { deep: true })
watch([current, regionExplorerMode], () => nextTick(renderRegionExplorerChart), { deep: true })
watch([current, salaryInsightMode, selectedSalaryMetric, selectedSkillMetric, filters], () => nextTick(renderSalaryInsightChart), { deep: true })
watch(activeTab, () => {
  if (activeTab.value === 'overview' || activeTab.value === 'region') nextTick(renderChinaMap)
  if (activeTab.value === 'demand') nextTick(renderDemandChart)
  if (activeTab.value === 'region') {
    nextTick(renderRegionChart)
    nextTick(renderRegionExplorerChart)
  }
  if (activeTab.value === 'salary') nextTick(renderSalaryInsightChart)
})
watch(() => props.initialTab, (tab) => { activeTab.value = tab })

function selectTab(tab) {
  if (activeTab.value === tab) return
  activeTab.value = tab
  emit('tab-change', tab)
}

onMounted(() => {
  loadDashboard()
  nextTick(renderChinaMap)
  nextTick(renderDemandChart)
  nextTick(renderRegionChart)
  nextTick(renderRegionExplorerChart)
  nextTick(renderSalaryInsightChart)
  window.addEventListener('resize', resizeChinaMap)
  window.addEventListener('resize', resizeDemandChart)
  window.addEventListener('resize', resizeRegionChart)
  window.addEventListener('resize', resizeRegionExplorerChart)
  window.addEventListener('resize', resizeSalaryInsightChart)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeChinaMap)
  window.removeEventListener('resize', resizeDemandChart)
  window.removeEventListener('resize', resizeRegionChart)
  window.removeEventListener('resize', resizeRegionExplorerChart)
  window.removeEventListener('resize', resizeSalaryInsightChart)
  if (dashboardRetryTimer) {
    clearTimeout(dashboardRetryTimer)
    dashboardRetryTimer = null
  }
  mapChart?.dispose()
  mapChart = null
  demandChart?.dispose()
  demandChart = null
  regionChart?.dispose()
  regionChart = null
  regionExplorerChart?.dispose()
  regionExplorerChart = null
  salaryInsightChart?.dispose()
  salaryInsightChart = null
})
</script>

<template>
  <section class="university-workspace university-dashboard">
    <header class="university-banner">
      <div class="university-banner-copy">
        <p class="eyebrow">高校就业分析</p>
        <h1>用岗位数据支撑就业指导。</h1>
        <p>查看岗位趋势、地区结构和学生就业准备情况，快速定位就业支持重点。</p>
      </div>
      <div class="university-banner-actions">
        <button class="university-button" type="button" title="退出高校端" @click="emit('logout')"><LogOut :size="15" /><span>退出登录</span></button>
        <div class="data-stamp"><Database :size="18" /><span>数据批次</span><strong>{{ current.statDate }}</strong></div>
      </div>
    </header>

    <nav class="university-tabs" aria-label="高校端分析页面">
      <button v-for="tab in tabs" :key="tab.key" type="button" :class="{ active: activeTab === tab.key }" @click="selectTab(tab.key)">{{ tab.label }}</button>
    </nav>

    <form v-if="activeTab !== 'students'" class="dashboard-controls" @submit.prevent="loadDashboard">
      <label v-if="showFilter('keyword')" class="dashboard-search"><Search :size="16" /><input v-model="filters.keyword" placeholder="搜索岗位、企业或技能" /></label>
      <SearchSelect v-if="showFilter('city')" v-model="filters.city" class="analysis-picker" label="地区筛选" placeholder="搜索省份或城市" empty-label="全部地区" :options="regionOptions" />
      <SearchSelect v-if="showFilter('industry')" v-model="filters.industry" class="analysis-picker" label="行业筛选" placeholder="搜索行业" empty-label="全部行业" :options="industryOptions" />
      <SearchSelect v-if="showFilter('education')" v-model="filters.education" class="analysis-picker" label="学历筛选" placeholder="搜索学历" empty-label="全部学历" :options="educationOptions" />
      <SearchSelect v-if="showFilter('category')" v-model="filters.category" class="analysis-picker" label="岗位方向" placeholder="搜索岗位方向" empty-label="全部方向" :options="categoryOptions" />
      <SearchSelect v-if="showFilter('companyScale')" v-model="filters.companyScale" class="analysis-picker" label="企业规模" placeholder="搜索企业规模" empty-label="全部规模" :options="companyScaleOptions" />
      <button class="command primary" type="submit" :disabled="loading"><LoaderCircle v-if="loading" class="spin" :size="16" /><RefreshCw v-else :size="16" />更新</button>
      <button class="command secondary" type="button" @click="resetFilters">重置</button>
    </form>

    <section v-if="activeTab !== 'students' && activeFilterChips.length" class="filter-status">
      <div class="filter-chips">
        <button v-for="item in activeFilterChips" :key="item.label" type="button" @click="clearFilter({ 关键词: 'keyword', 地区: 'city', 行业: 'industry', 学历: 'education', 岗位方向: 'category', 企业规模: 'companyScale' }[item.label])">{{ item.label }}：{{ item.value }}</button>
      </div>
    </section>

    <div v-if="sourceNotice && activeTab !== 'students'" class="university-info"><CircleAlert :size="18" /><span>{{ sourceNotice }}</span></div>
    <div v-if="loading && !dashboard && activeTab !== 'students'" class="workspace-loading"><LoaderCircle :size="28" /><span>正在聚合高校端市场看板</span></div>

    <template v-if="activeTab === 'overview'">
      <section class="dashboard-kpis" aria-label="高校端核心指标">
        <div v-for="item in kpis" :key="item.label" class="kpi-card" tabindex="0">
          <component :is="item.icon" :size="18" />
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <aside class="kpi-tooltip" role="tooltip">
            <b>{{ item.label }}</b>
            <p v-for="line in item.detail" :key="line">{{ line }}</p>
          </aside>
        </div>
      </section>

      <section class="dashboard-map-section">
        <div class="dashboard-panel province-panel china-map-panel">
          <div class="university-section-head">
            <div><p class="eyebrow">地区热力</p><h2>省级岗位需求分布</h2></div>
            <div class="metric-toggle" role="group" aria-label="地图指标切换">
              <button type="button" :class="{ active: selectedProvinceMetric === 'jobCount' }" @click="selectedProvinceMetric = 'jobCount'">岗位数</button>
              <button type="button" :class="{ active: selectedProvinceMetric === 'salary' }" @click="selectedProvinceMetric = 'salary'">平均薪资</button>
            </div>
          </div>
          <div ref="mapElement" class="china-map-canvas" aria-label="地区岗位需求热力图"></div>
        </div>

        <aside class="dashboard-panel province-insight-panel">
          <div class="university-section-head"><div><p class="eyebrow">地区岗位结构占比</p><h2>{{ selectedProvinceCell?.name || '暂无地区' }}岗位结构</h2></div><MapPinned :size="21" /></div>
          <div class="province-metrics">
            <div><span>岗位数</span><strong>{{ formatNumber(selectedProvinceCell?.jobCount) }}</strong></div>
            <div><span>平均薪资</span><strong>{{ salaryValue(selectedProvinceCell?.averageSalary) }}</strong></div>
          </div>
          <div class="donut-layout compact-donut">
            <div class="donut-chart" :style="donutStyle(selectedProvinceCategories, 'jobCount', 'key')"><span>{{ selectedProvinceCategories.length }}</span></div>
            <div class="donut-list">
              <button v-for="item in selectedProvinceCategories" :key="item.key" type="button" @click="selectedFamily = item.key">
                <i :style="{ background: familyColors[item.key] || '#87949a' }"></i><span>{{ item.key }}</span><strong>{{ formatNumber(item.jobCount) }}</strong>
                <aside class="category-tooltip" role="tooltip">
                  <b>{{ categoryTooltip(item).title }}</b>
                  <p>典型岗位：{{ categoryTooltip(item).typicalJobs }}</p>
                  <p>判断标准：{{ categoryTooltip(item).rule }}</p>
                  <p>当前岗位数：{{ formatNumber(categoryTooltip(item).jobCount) }}</p>
                </aside>
              </button>
            </div>
          </div>
          <ol class="province-top-list">
            <li v-for="item in selectedProvinceIndustries" :key="`${item.x}-${item.y}`"><span>{{ item.y }}</span><strong>{{ formatNumber(item.jobCount) }}</strong></li>
            <li v-if="!selectedProvinceIndustries.length"><span>暂无行业明细</span><strong>-</strong></li>
          </ol>
          <p class="panel-note">在地图上悬停可看迷你说明，点击省份会更新这里的地区结构。</p>
        </aside>
      </section>

      <section class="dashboard-two-column compact">
        <div class="dashboard-panel">
          <div class="university-section-head"><div><p class="eyebrow">热门地区</p><h2>岗位集中地区</h2></div></div>
          <ol class="metric-list interactive">
            <li v-for="item in current.cities.slice(0, 8)" :key="item.key"><button type="button" @click="drillIntoCity(item.key)"><b>{{ item.key }}</b><i><em :style="{ width: widthFor(item.jobCount, current.cities) }"></em></i><strong>{{ formatNumber(item.jobCount) }}</strong></button></li>
          </ol>
        </div>
        <div class="dashboard-panel">
          <div class="university-section-head"><div><p class="eyebrow">热门行业</p><h2>行业需求排行</h2></div></div>
          <ol class="metric-list interactive">
            <li v-for="item in current.industries.slice(0, 8)" :key="item.key"><button type="button" :class="{ active: selectedIndustryMetric?.key === item.key }" @click="selectedIndustry = item.key"><b>{{ item.key }}</b><i><em :style="{ width: widthFor(item.jobCount, current.industries) }"></em></i><strong>{{ formatNumber(item.jobCount) }}</strong></button></li>
          </ol>
        </div>
      </section>

      <section class="dashboard-panel overview-family-panel">
          <div class="university-section-head"><div><p class="eyebrow">岗位结构</p><h2>岗位大类占比</h2></div><ChartNoAxesCombined :size="21" /></div>
          <div class="donut-layout">
            <div class="donut-chart" :style="donutStyle(filteredFamilyMetrics)"><span>{{ filteredFamilyMetrics.length }}</span></div>
            <div class="donut-list">
              <button v-for="item in filteredFamilyMetrics" :key="item.family" type="button" :class="{ active: selectedFamilyMetric?.family === item.family }" @click="selectedFamily = item.family">
                <i :style="{ background: familyColors[item.family] }"></i><span>{{ item.family }}</span><strong>{{ formatNumber(item.jobCount) }}</strong>
                <aside class="category-tooltip" role="tooltip">
                  <b>{{ categoryTooltip(item).title }}</b>
                  <p>典型岗位：{{ categoryTooltip(item).typicalJobs }}</p>
                  <p>判断标准：{{ categoryTooltip(item).rule }}</p>
                  <p>当前岗位数：{{ formatNumber(categoryTooltip(item).jobCount) }}</p>
                </aside>
              </button>
            </div>
          </div>
      </section>
    </template>

    <template v-else-if="activeTab === 'demand'">
      <section class="demand-kpi-strip">
        <div tabindex="0"><span>热门岗位</span><strong>{{ current.hotJobs.length }}</strong><small>{{ selectedJobMetric?.key || '暂无岗位' }}</small><aside class="mini-tooltip" role="tooltip">统计当前筛选下的热门岗位条目数量，下面显示当前选中的岗位。</aside></div>
        <div tabindex="0"><span>岗位大类</span><strong>{{ filteredFamilyMetrics.length }}</strong><small>{{ selectedFamilyMetric?.family || '暂无大类' }}</small><aside class="mini-tooltip" role="tooltip">统计岗位被归并后的大类数量，便于看市场结构是否集中。</aside></div>
        <div tabindex="0"><span>技能覆盖</span><strong>{{ ratio(current.summary.skillJobCount, current.summary.jobCount) }}</strong><small>{{ topNames(current.hotSkills, 3) }}</small><aside class="mini-tooltip" role="tooltip">有技能标签的岗位占比，下面显示当前结果里的高频技能。</aside></div>
        <div tabindex="0"><span>主要薪资</span><strong>{{ salaryValue(current.summary.averageSalary) }}</strong><small>中位数 {{ salaryValue(current.summary.medianSalary) }}</small><aside class="mini-tooltip" role="tooltip">当前筛选结果的平均月薪，下面补充中位数作为更稳的参考。</aside></div>
      </section>

      <section class="demand-visual-layout">
        <div class="dashboard-panel demand-chart-panel">
          <div class="university-section-head">
            <div><p class="eyebrow">岗位需求图谱</p><h2>多视角岗位结构分析</h2></div>
            <div class="metric-toggle chart-toggle" role="group" aria-label="岗位需求图表类型切换">
              <button v-for="mode in demandChartModes" :key="mode.key" type="button" :class="{ active: demandChartMode === mode.key }" @click="demandChartMode = mode.key">{{ mode.label }}<aside class="mode-tooltip" role="tooltip">{{ mode.hint }}</aside></button>
            </div>
          </div>
          <div ref="demandChartElement" class="demand-chart-canvas" aria-label="岗位需求多模式统计图"></div>
        </div>

        <aside class="dashboard-panel demand-detail-panel">
          <div class="university-section-head"><div><p class="eyebrow">当前选择</p><h2>{{ selectedJobMetric?.key || selectedFamilyMetric?.family || '暂无' }}</h2></div><BriefcaseBusiness :size="21" /></div>
          <div class="demand-profile">
            <div><span>岗位数</span><strong>{{ formatNumber(selectedJobMetric?.jobCount || selectedFamilyMetric?.jobCount) }}</strong></div>
            <div><span>薪资参考</span><strong>{{ salaryRange(selectedJobMetric) }}</strong></div>
            <div><span>所属大类</span><strong>{{ selectedFamilyMetric?.family || '暂无' }}</strong></div>
            <div><span>热门技能</span><strong>{{ topNames(current.hotSkills, 3) }}</strong></div>
          </div>
          <p class="panel-note">点击主图中的岗位或大类会联动这里；右上角可切换排行、矩形树、流向、气泡、热力和雷达视角。</p>
          <div class="tag-row"><em v-for="item in selectedFamilyMetric?.categories || []" :key="item.key">{{ item.key }} {{ formatNumber(item.jobCount) }}</em></div>
        </aside>
      </section>

      <section class="dashboard-two-column compact">
        <div class="dashboard-panel demand-list-panel">
          <div class="university-section-head"><div><p class="eyebrow">岗位需求</p><h2>热门岗位 Top 20</h2></div><BriefcaseBusiness :size="21" /></div>
          <ol class="metric-list wide interactive">
            <li v-for="item in current.hotJobs" :key="item.key"><button type="button" :class="{ active: selectedJobMetric?.key === item.key }" @click="selectedJob = item.key"><b>{{ item.key }}</b><i><em :style="{ width: widthFor(item.jobCount, current.hotJobs) }"></em></i><strong>{{ formatNumber(item.jobCount) }}</strong><small>{{ salaryRange(item) }}</small></button></li>
          </ol>
        </div>
        <div class="dashboard-panel">
          <div class="university-section-head"><div><p class="eyebrow">岗位大类</p><h2>需求结构与归并规则</h2></div><ChartNoAxesCombined :size="21" /></div>
          <div class="family-cards">
            <button v-for="item in current.categoryFamilies" :key="item.family" type="button" :class="{ active: selectedFamilyMetric?.family === item.family }" @click="selectedFamily = item.family">
              <span :style="{ background: familyColors[item.family] }"></span>
              <strong>{{ item.family }}</strong>
              <b>{{ formatNumber(item.jobCount) }}</b>
              <small>{{ item.rule }}</small>
            </button>
          </div>
          <article class="detail-card">
            <span>当前大类</span>
            <strong>{{ selectedFamilyMetric?.family || '暂无' }}</strong>
            <p>典型岗位：{{ selectedFamilyMetric?.typicalJobs?.join('、') || '暂无' }}</p>
            <div class="tag-row"><em v-for="item in selectedFamilyMetric?.categories || []" :key="item.key">{{ item.key }} {{ formatNumber(item.jobCount) }}</em></div>
          </article>
        </div>
      </section>

      <section class="dashboard-panel rule-panel demand-rule-panel">
        <div class="university-section-head"><div><p class="eyebrow">标准化归类</p><h2>岗位大类归并规则</h2></div></div>
        <div class="category-rule-table">
          <div class="rule-head">大类</div><div class="rule-head">包含的典型岗位</div><div class="rule-head">判断标准</div>
          <template v-for="item in current.categoryFamilies" :key="item.family">
            <strong>{{ item.family }}</strong>
            <span>{{ item.typicalJobs.join('、') }}</span>
            <em>{{ item.rule }}</em>
          </template>
        </div>
      </section>
    </template>

    <template v-else-if="activeTab === 'region'">
      <section class="dashboard-panel province-panel region-map-panel">
        <div class="university-section-head">
          <div><p class="eyebrow">地区 × 指标</p><h2>省级岗位需求分布</h2></div>
          <div class="metric-toggle" role="group" aria-label="地区图指标切换">
            <button type="button" :class="{ active: selectedProvinceMetric === 'jobCount' }" @click="selectedProvinceMetric = 'jobCount'">岗位数</button>
            <button type="button" :class="{ active: selectedProvinceMetric === 'salary' }" @click="selectedProvinceMetric = 'salary'">平均薪资</button>
          </div>
        </div>
        <div ref="mapElement" class="china-map-canvas region-map-canvas" aria-label="地区岗位需求热力图"></div>
      </section>
      <section class="dashboard-panel region-detail-window">
        <div class="university-section-head">
          <div><p class="eyebrow">地区画像</p><h2>{{ selectedProvinceCell?.name || '暂无地区' }}详细信息</h2></div>
          <div class="metric-toggle" role="group" aria-label="地区画像图切换">
            <button v-for="mode in regionChartModes" :key="mode.key" type="button" :class="{ active: regionChartMode === mode.key }" @click="regionChartMode = mode.key">{{ mode.label }}<aside class="mode-tooltip" role="tooltip">{{ mode.hint }}</aside></button>
          </div>
        </div>
        <div class="region-detail-layout">
          <article class="region-story-card">
            <div class="region-profile-media">
              <div>
                <span>地区档案</span>
                <strong>{{ regionProfile.name }}</strong>
              </div>
            </div>
            <div class="region-profile-copy">
              <p>{{ regionProfile.summary }}</p>
            </div>
            <div class="region-story-metrics">
              <div><span>岗位数</span><strong>{{ formatNumber(selectedProvinceOverview.jobCount) }}</strong></div>
              <div><span>平均薪资</span><strong>{{ salaryValue(selectedProvinceOverview.averageSalary) }}</strong></div>
              <div><span>行业数</span><strong>{{ selectedProvinceOverview.industryCount }}</strong></div>
              <div><span>大类数</span><strong>{{ selectedProvinceOverview.categoryCount }}</strong></div>
            </div>
            <div class="region-profile-section">
              <span>产业关注</span>
              <div class="tag-row"><em v-for="item in regionProfile.industryFocus" :key="item">{{ item }}</em></div>
            </div>
            <div class="region-profile-section">
              <span>高校端关注</span>
              <ul class="region-bullet-list"><li v-for="item in regionProfile.universityFocus" :key="item">{{ item }}</li></ul>
            </div>
            <div class="region-link-row">
              <a v-for="item in regionProfile.links" :key="item.url" :href="item.url" target="_blank" rel="noreferrer">{{ item.label }}</a>
            </div>
          </article>
          <div class="region-chart-panel">
            <div ref="regionChartElement" class="region-detail-chart" aria-label="地区详情统计图"></div>
            <div class="region-context-strip">
              <div>
                <span>高校投放建议</span>
                <p>结合本地区热门行业和岗位大类，优先安排宣讲、实习基地和课程案例对接。</p>
              </div>
              <div>
                <span>资料补充口径</span>
                <p>毕业生与待就业数据待接入校级就业系统。</p>
              </div>
            </div>
            <div class="region-note-grid">
              <div tabindex="0"><span>热门行业</span><strong>{{ selectedProvinceIndustries.slice(0, 3).map((item) => item.y).join('、') || '暂无' }}</strong><aside class="mini-tooltip" role="tooltip">来自当前岗位样本中该地区行业岗位数排序，用来判断就业需求集中方向。</aside></div>
              <div tabindex="0"><span>结构标签</span><strong>{{ topNames(selectedProvinceCategories, 3) }}</strong><aside class="mini-tooltip" role="tooltip">来自岗位大类归并结果，帮助高校判断本地区更偏技术、运营、市场还是服务类需求。</aside></div>
              <div tabindex="0"><span>代表企业</span><strong>{{ regionProfile.companies.join('、') }}</strong><aside class="mini-tooltip" role="tooltip">作为校企合作和宣讲邀约线索，不代表严格招聘量排名。</aside></div>
              <div tabindex="0"><span>代表高校</span><strong>{{ regionProfile.universities.join('、') }}</strong><aside class="mini-tooltip" role="tooltip">用于识别本地区高校资源和潜在联动对象，不代表学校排名。</aside></div>
            </div>
          </div>
        </div>
      </section>
      <section class="dashboard-panel region-explorer-panel">
        <div class="university-section-head">
          <div><p class="eyebrow">地区钻取大图</p><h2>重点地区结构与行业热力</h2></div>
          <div class="metric-toggle chart-toggle" role="group" aria-label="地区钻取图切换">
            <button v-for="mode in regionExplorerModes" :key="mode.key" type="button" :class="{ active: regionExplorerMode === mode.key }" @click="regionExplorerMode = mode.key">{{ mode.label }}<aside class="mode-tooltip" role="tooltip">{{ mode.hint }}</aside></button>
          </div>
        </div>
        <div class="region-explorer-summary">
          <div><span>覆盖地区</span><strong>{{ current.regionalCategoryShares.length }}</strong></div>
          <div><span>可视行业</span><strong>{{ unique(current.cityIndustryHeatmap.map((item) => item.y)).length }}</strong></div>
          <div><span>当前主省</span><strong>{{ selectedProvinceCell?.name || '暂无' }}</strong></div>
        </div>
        <div ref="regionExplorerElement" class="region-explorer-canvas" aria-label="地区钻取大图"></div>
        <div class="region-explorer-footnote">
          <div v-if="regionExplorerMode === 'structure'">大图按地区岗位大类结构展开，右上切换后可看行业热力。</div>
          <div v-else>大图按地区 × 行业热力展开，点击色块会联动地区与行业筛选。</div>
        </div>
      </section>
    </template>

    <template v-else-if="activeTab === 'salary'">
      <section class="dashboard-panel salary-insight-panel">
        <div class="university-section-head">
          <div><p class="eyebrow">薪资 × 学历 × 技能</p><h2>岗位门槛与训练信号</h2></div>
          <div class="metric-toggle chart-toggle" role="group" aria-label="薪资技能图切换">
            <button v-for="mode in salaryInsightModes" :key="mode.key" type="button" :class="{ active: salaryInsightMode === mode.key }" @click="salaryInsightMode = mode.key">{{ mode.label }}<aside class="mode-tooltip" role="tooltip">{{ mode.hint }}</aside></button>
          </div>
        </div>
        <div class="salary-insight-layout">
          <div class="salary-chart-shell">
            <div ref="salaryInsightChartElement" class="salary-insight-chart" aria-label="薪资技能分析图"></div>
          </div>
          <aside class="salary-side-panel">
            <template v-if="salaryInsightMode === 'salary'">
              <span>当前薪资区间</span>
              <strong>{{ selectedSalaryMetric?.key || '暂无' }}</strong>
              <p>该区间包含 {{ formatNumber(selectedSalaryMetric?.jobCount) }} 个岗位。薪资分布更适合和学历、地区一起判断岗位门槛。</p>
              <div class="tag-row"><em v-for="item in current.cities.slice(0, 4)" :key="item.key">{{ item.key }} {{ salaryRange(item) }}</em></div>
            </template>
            <template v-else-if="salaryInsightMode === 'education'">
              <span>学历门槛</span>
              <strong>{{ filters.education || current.education?.[0]?.key || '暂无' }}</strong>
              <p>学历要求用于判断岗位进入门槛。点击图中学历可先选中条件，再点更新进行筛选。</p>
              <div class="tag-row"><em v-for="item in current.education.slice(0, 5)" :key="item.key">{{ item.key }} {{ formatNumber(item.jobCount) }}</em></div>
            </template>
            <template v-else>
              <span>当前技能</span>
              <strong>{{ selectedSkillMetric?.key || '暂无' }}</strong>
              <p>{{ formatNumber(selectedSkillMetric?.jobCount) }} 个岗位提及，可作为岗位训练需求的辅助参考。</p>
              <div class="tag-row"><em v-for="item in current.hotSkills.slice(0, 6)" :key="item.key">{{ item.key }} {{ formatNumber(item.jobCount) }}</em></div>
            </template>
          </aside>
        </div>
      </section>
      <IndustrySalaryPanel :api-base="props.apiBase" :city="filters.city" />
      <section class="dashboard-two-column compact salary-support-grid">
        <div class="dashboard-panel">
          <div class="university-section-head"><div><p class="eyebrow">结构补充</p><h2>{{ salaryInsightMode === 'skills' ? '高频技能列表' : '地区薪资对比' }}</h2></div></div>
          <ol v-if="salaryInsightMode === 'skills'" class="metric-list interactive">
            <li v-for="item in current.hotSkills.slice(0, 10)" :key="item.key"><button type="button" :class="{ active: selectedSkillMetric?.key === item.key }" @click="selectedSkill = item.key"><b>{{ item.key }}</b><i><em :style="{ width: widthFor(item.jobCount, current.hotSkills) }"></em></i><strong>{{ formatNumber(item.jobCount) }}</strong></button></li>
          </ol>
          <ol v-else class="metric-list interactive">
            <li v-for="item in current.cities.slice(0, 8)" :key="item.key"><button type="button" @click="drillIntoCity(item.key)"><b>{{ item.key }}</b><i><em :style="{ width: widthFor(item.jobCount, current.cities) }"></em></i><strong>{{ salaryRange(item) }}</strong></button></li>
          </ol>
        </div>
        <div class="dashboard-panel">
          <div class="university-section-head"><div><p class="eyebrow">高校端解释</p><h2>可行动建议</h2></div><Lightbulb :size="21" /></div>
          <ol class="guidance-list">
            <li v-for="(item, index) in current.suggestions" :key="item"><span>{{ String(index + 1).padStart(2, '0') }}</span><p>{{ item }}</p></li>
          </ol>
        </div>
      </section>
    </template>

    <UniversityStudentOverview v-else :api-base="props.apiBase" :initial-page="props.initialStudentPage" @page-change="emit('student-page-change', $event)" />
  </section>
</template>
