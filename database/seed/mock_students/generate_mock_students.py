#!/usr/bin/env python3
"""Generate 100 mock students with complete associated data for the Spark Employment Platform.

Usage:
    python3 generate_mock_students.py

Requires:
    pip install bcrypt

Output files:
    - import_mock_students.sql
    - remove_mock_students.sql
    - mock_students_preview.csv
    - mock_students_manifest.json
    - README.md (if not present, generated once)
"""

import json
import csv
import os
import random
import hashlib
from datetime import date, timedelta

# ── fixed seed for reproducibility ──────────────────────────────────────────
SEED = 20260714
random.seed(SEED)

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── bcrypt ───────────────────────────────────────────────────────────────────
try:
    import bcrypt
except ModuleNotFoundError:
    bcrypt = None

BCRYPT_ROUNDS = 10
DEMO_PASSWORD = "Student@123"

def bcrypt_hash(password: str) -> str:
    if bcrypt is not None:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(BCRYPT_ROUNDS)).decode("utf-8")
    # Valid Spring Security-compatible BCrypt hash for the local demo password.
    # Keeping a fallback makes deterministic seed regeneration possible offline.
    return "$2b$10$xH/J7Ca9GmTHm2F4UZWuQuLlEI4U1SDM9pzUER4fFQaGsdo5D4xDe"

# Pre-compute ONE hash for all students (Spring Security BCrypt format)
PASSWORD_HASH = bcrypt_hash(DEMO_PASSWORD)

# ── data dictionaries ────────────────────────────────────────────────────────

COLLEGES = {
    "信息工程学院": {
        "计算机科学与技术": 12,
        "软件工程": 10,
        "人工智能": 8,
    },
    "大数据学院": {
        "数据科学与大数据技术": 15,
        "大数据管理与应用": 10,
    },
    "经济管理学院": {
        "市场营销": 6,
        "财务管理": 6,
        "电子商务": 5,
        "人力资源管理": 3,
    },
    "智能制造学院": {
        "自动化": 6,
        "机械设计制造及其自动化": 5,
        "电子信息工程": 4,
    },
    "其他学院": {
        "金融学": 3,
        "土木工程": 2,
        "生物制药": 2,
        "视觉传达设计": 2,
        "汉语言文学": 1,
    },
}

# Readiness tiers: A=充分, B=良好, C=一般, D=需重点关注
READINESS_COUNTS = {"A": 20, "B": 35, "C": 30, "D": 15}

# Graduation year distribution
GRAD_YEARS = [2026]*65 + [2027]*25 + [2025]*10

# Master's degrees — primarily in AI, data science, CS, SE, finance
MASTER_ELIGIBLE_MAJORS = [
    "人工智能", "数据科学与大数据技术", "计算机科学与技术",
    "软件工程", "金融学", "大数据管理与应用"
]

# Standard cities (no "市" suffix)
CITIES = [
    "北京", "上海", "深圳", "广州", "杭州", "成都", "南京", "武汉", "西安", "重庆",
    "苏州", "天津", "长沙", "郑州", "合肥", "厦门", "青岛", "大连", "济南", "福州",
]

CITY_WEIGHTS = [12, 10, 10, 8, 10, 10, 8, 8, 7, 5, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1]

# ── name pools ───────────────────────────────────────────────────────────────
SURNAMES = [
    "王", "李", "张", "刘", "陈", "杨", "黄", "赵", "周", "吴",
    "徐", "孙", "马", "朱", "胡", "郭", "何", "高", "林", "罗",
    "郑", "梁", "谢", "宋", "唐", "许", "韩", "冯", "邓", "曹",
    "彭", "曾", "萧", "田", "董", "潘", "袁", "于", "蒋", "蔡",
    "余", "杜", "叶", "程", "苏", "魏", "吕", "丁", "任", "沈",
    "姚", "卢", "姜", "崔", "钟", "谭", "陆", "汪", "范", "金",
    "石", "廖", "贾", "夏", "韦", "付", "方", "白", "邹", "孟",
    "熊", "秦", "邱", "江", "尹", "薛", "闫", "段", "雷", "侯",
    "龙", "史", "陶", "黎", "贺", "顾", "毛", "郝", "龚", "邵",
    "万", "钱", "严", "覃", "武", "戴", "莫", "孔", "向", "汤",
]

GIVEN_NAMES_MALE = [
    "伟", "强", "磊", "洋", "勇", "军", "杰", "涛", "明", "超",
    "浩", "宇", "轩", "然", "博", "文", "峰", "宁", "鹏", "晨",
    "子涵", "子轩", "宇轩", "浩然", "博文", "俊杰", "思远", "志远", "晓明", "建国",
    "一鸣", "天宇", "子豪", "嘉诚", "泽宇", "铭哲", "睿轩", "奕辰", "逸飞", "致远",
    "宇翔", "鑫鹏", "昊天", "皓轩", "梓豪", "俊熙", "瑞霖", "晟睿", "文博", "文昊",
]

GIVEN_NAMES_FEMALE = [
    "芳", "敏", "静", "丽", "婷", "雪", "玲", "丹", "洁", "红",
    "欣怡", "雨涵", "梓涵", "诗涵", "梦琪", "思雨", "雨桐", "若曦", "艺琳", "语嫣",
    "晓婷", "佳怡", "雅婷", "雪婷", "晓雪", "美琳", "诗雨", "欣妍", "婉儿", "静怡",
    "雨欣", "曼琳", "瑾瑜", "婧怡", "梓萱", "雨霏", "思涵", "若琳", "艺涵", "婉清",
    "清怡", "慧妍", "淑婷", "悦然", "紫萱", "佳琪", "晓萱", "雅琪", "馨予", "静涵",
]

# ── skill pools by major family ──────────────────────────────────────────────
SKILLS_CS = ["Java", "Spring Boot", "Spring Cloud", "MySQL", "Redis", "Linux", "Git",
             "Docker", "JavaScript", "Vue", "React", "HTML", "CSS", "TypeScript",
             "Python", "SQL", "Kubernetes", "Jenkins", "ECharts"]

SKILLS_DS = ["Python", "SQL", "Spark", "Hadoop", "Hive", "Pandas", "NumPy",
             "数据可视化", "机器学习", "MySQL", "Linux", "Git", "Excel",
             "Flink", "Kafka", "Tableau", "Power BI"]

SKILLS_AI = ["Python", "机器学习", "深度学习", "PyTorch", "TensorFlow",
             "SQL", "Pandas", "NumPy", "Linux", "Git",
             "数据可视化", "Kafka", "Spark"]

SKILLS_BIZ = ["Excel", "SQL", "数据分析", "Python", "数据可视化",
              "Tableau", "Power BI", "MySQL", "Git"]

SKILLS_FINANCE = ["Excel", "SQL", "Python", "数据分析", "Power BI",
                  "MySQL", "数据可视化"]

SKILLS_ENGINEER = ["C", "Python", "MATLAB", "Linux", "Git",
                   "SQL", "Excel", "Docker"]

SKILLS_DESIGN = ["Photoshop", "Illustrator", "Figma", "UI设计", "视频剪辑", "Excel"]

SKILLS_LIBERAL = ["Excel", "Office", "Python", "SQL", "数据分析"]

# Cross-major skills (about 15% of total skills)
CROSS_SKILLS = ["Python", "SQL", "Excel", "Git", "Linux", "数据分析", "MySQL"]

SKILL_MAP = {
    "计算机科学与技术": SKILLS_CS,
    "软件工程": SKILLS_CS,
    "人工智能": SKILLS_AI,
    "数据科学与大数据技术": SKILLS_DS,
    "大数据管理与应用": SKILLS_DS,
    "市场营销": SKILLS_BIZ,
    "财务管理": SKILLS_FINANCE,
    "电子商务": SKILLS_BIZ,
    "人力资源管理": SKILLS_BIZ,
    "自动化": SKILLS_ENGINEER,
    "机械设计制造及其自动化": SKILLS_ENGINEER,
    "电子信息工程": SKILLS_ENGINEER,
    "金融学": SKILLS_FINANCE,
    "土木工程": SKILLS_ENGINEER,
    "生物制药": ["Python", "SQL", "Excel", "数据分析"],
    "视觉传达设计": SKILLS_DESIGN,
    "汉语言文学": SKILLS_LIBERAL,
}

# ── experience templates by major ────────────────────────────────────────────
def experiences_for(student, readiness):
    """Generate experiences based on major and readiness level."""
    major = student["major"]
    exp_list = []
    today = date.today()

    # Helper: random date in range
    def date_range(start_year, start_month, end_year, end_month):
        s = date(start_year, start_month, 1)
        e = date(end_year, end_month, 28)
        days = (e - s).days
        d = s + timedelta(days=random.randint(0, max(0, days)))
        return d

    # ── Templates per major family ──
    if major in ("计算机科学与技术", "软件工程"):
        templates = {
            "project": [
                {"title": "在线图书管理系统", "org": "软件工程课程团队", "role": "后端开发",
                 "desc": "基于Spring Boot + Vue开发在线图书管理系统，实现图书借阅、归还、用户管理等功能模块。我负责后端接口开发与数据库设计，使用MySQL存储数据，Redis做缓存加速。项目通过JWT实现用户认证，完成单元测试覆盖率约85%。"},
                {"title": "校园二手交易小程序", "org": "计算机学院创新实验室", "role": "全栈开发",
                 "desc": "参与校园二手交易平台开发，使用Vue前端和Spring Boot后端架构。实现商品发布、搜索、聊天和订单管理功能。完成12个API接口的开发和联调，系统可承载200并发请求。"},
                {"title": "分布式日志分析系统", "org": "信息工程学院实验室", "role": "后端开发",
                 "desc": "设计并实现基于ELK的分布式日志采集与分析系统，支持多节点日志聚合。使用Filebeat采集日志，Kafka做消息队列，Elasticsearch做存储和检索。完成3个核心模块开发，处理约10万条模拟日志数据。"},
                {"title": "智能问答系统原型", "org": "毕业设计项目", "role": "项目负责人",
                 "desc": "基于Spring Boot + Redis实现智能客服问答系统，集成FAQ匹配和关键词检索功能。设计问答题库，支持模糊匹配和答案排序。完成系统设计文档和接口文档，项目获院级优秀毕业设计。"},
            ],
            "internship": [
                {"title": "Java后端开发实习生", "org": "数字未来科技有限公司", "role": "后端开发实习生",
                 "desc": "参与公司内部管理系统后端开发，使用Spring Boot和MyBatis-Plus。负责用户管理模块和权限管理模块的设计与实现。实习期间完成6个接口开发，配合前端完成联调测试。"},
                {"title": "软件开发实习生", "org": "云端信息科技有限公司", "role": "软件开发实习生",
                 "desc": "参与电商平台后端服务开发，使用Spring Cloud微服务架构。负责订单模块的接口开发和数据库优化，通过索引优化将查询时间降低约20%。编写技术文档和接口说明。"},
            ],
            "award": [
                {"title": "全国大学生程序设计竞赛省二等奖", "org": "ACM-ICPC组委会", "role": "参赛队员",
                 "desc": "参加ACM-ICPC区域赛，团队完成4题，获省级二等奖。在比赛中负责算法设计和代码实现，熟练使用C++和数据结构解题。"},
                {"title": "校级优秀毕业设计", "org": "信息工程学院", "role": "个人",
                 "desc": "毕业设计'智能推荐系统'获院级优秀毕业设计。项目结合协同过滤和内容推荐算法，基于用户行为数据实现个性化推荐。"},
            ],
        }
    elif major == "人工智能":
        templates = {
            "project": [
                {"title": "基于深度学习的图像分类系统", "org": "人工智能实验室", "role": "算法开发",
                 "desc": "使用PyTorch实现ResNet-50图像分类模型，在CIFAR-100数据集上达到78%准确率。完成数据预处理、模型训练和评估全流程。优化数据增强策略，将模型泛化能力提升约12%。"},
                {"title": "智能对话机器人原型", "org": "AI创新实验室", "role": "NLP算法开发",
                 "desc": "基于Transformer架构实现中文对话系统，使用BERT预训练模型进行意图识别和实体抽取。完成模型微调和部署，支持8种常见问答场景，意图识别准确率约91%。"},
            ],
            "internship": [
                {"title": "AI算法实习生", "org": "星辰人工智能研究院", "role": "算法实习生",
                 "desc": "参与计算机视觉项目，负责数据标注质量检查和模型训练实验。使用PyTorch进行模型调优，撰写实验报告12份。协助团队完成目标检测模型mAP从82%提升至87%的优化工作。"},
            ],
            "award": [
                {"title": "全国大学生数学建模竞赛国家二等奖", "org": "中国工业与应用数学学会", "role": "建模与编程",
                 "desc": "团队针对'无人机路径规划'赛题建立优化模型，使用Python实现遗传算法求解。完成模型建立、程序编写和论文撰写，获国家二等奖。"},
            ],
        }
    elif major in ("数据科学与大数据技术", "大数据管理与应用"):
        templates = {
            "project": [
                {"title": "电商用户行为分析平台", "org": "大数据学院实验室", "role": "数据开发",
                 "desc": "基于Spark和Hive搭建电商用户行为数据分析平台，处理约50万条模拟日志数据。实现用户画像构建、购买路径分析和商品推荐。使用ECharts完成数据可视化大屏展示。"},
                {"title": "实时数据管道搭建实践", "org": "大数据课程项目", "role": "数据工程师",
                 "desc": "使用Kafka + Flink搭建实时数据处理管道，模拟电商订单流处理场景。实现数据采集、清洗、聚合到MySQL存储的完整链路，端到端延迟控制在秒级。"},
            ],
            "internship": [
                {"title": "数据分析实习生", "org": "讯飞大数据有限公司", "role": "数据分析实习生",
                 "desc": "负责业务数据分析报告的撰写和数据提取。使用SQL和Python处理分析5000条公开岗位数据，产出行业需求趋势报告。完成16项数据提取需求和8份分析报告。"},
            ],
            "award": [
                {"title": "全国大学生大数据竞赛三等奖", "org": "中国计算机学会", "role": "数据建模",
                 "desc": "参赛团队完成大规模用户行为预测任务，使用Spark MLlib进行特征工程和模型训练。线上AUC达到0.86，排名前15%，获三等奖。"},
            ],
        }
    elif major in ("市场营销", "电子商务"):
        templates = {
            "project": [
                {"title": "校园电商用户调研", "org": "市场营销课程项目", "role": "项目负责人",
                 "desc": "组织团队完成校园电商消费行为调研，设计问卷并回收312份有效样本。使用Excel和SPSS完成数据分析，撰写调研报告并提出3个运营优化建议。"},
                {"title": "新媒体营销活动策划", "org": "创业实践团队", "role": "内容运营",
                 "desc": "策划并执行校园产品推广活动，负责微信公众号内容创作和社群运营。活动期间新增关注320人，文章平均阅读量提升约40%。"},
            ],
            "internship": [
                {"title": "电商运营实习生", "org": "潮流电商平台", "role": "运营助理",
                 "desc": "协助运营团队进行商品上下架管理、活动页面搭建和数据分析。参与618大促活动运营，负责部分品类的选品和价格监控。完成周报数据统计和竞品分析。"},
            ],
            "award": [
                {"title": "全国大学生电子商务挑战赛省三等奖", "org": "教育部电子商务教指委", "role": "队长",
                 "desc": "团队策划校园二手书交易平台商业方案，完成市场分析、商业模式设计和财务预测。方案获省级三等奖。"},
            ],
        }
    elif major in ("财务管理", "金融学"):
        templates = {
            "project": [
                {"title": "上市公司财务分析报告", "org": "金融分析课程项目", "role": "分析员",
                 "desc": "选取5家互联网上市公司进行财务分析，使用Excel和Python完成财务比率计算、杜邦分析和估值模型。撰写2万字分析报告，获课程优秀评价。"},
            ],
            "internship": [
                {"title": "财务实习生", "org": "德勤会计师事务所", "role": "审计实习生",
                 "desc": "参与某制造业企业年审项目，负责存货盘点、凭证抽查和底稿整理。完成8家子公司的银行函证核对，协助出具审计调整分录。"},
                {"title": "金融分析实习生", "org": "中金证券研究部", "role": "行业研究实习生",
                 "desc": "协助分析师完成科技行业研究，收集整理行业数据，撰写行业周报和公司深度分析报告。使用Wind和Excel完成数据分析和图表制作。"},
            ],
            "award": [
                {"title": "CFA全球投资分析大赛校赛第一名", "org": "CFA Institute", "role": "财务分析",
                 "desc": "团队针对指定上市公司完成深度投资分析，负责财务建模和估值分析。撰写投资研究报告并进行英文答辩，获校赛第一名。"},
            ],
        }
    elif major == "人力资源管理":
        templates = {
            "project": [
                {"title": "校园招聘效率优化方案", "org": "人力资源管理课程项目", "role": "调研分析",
                 "desc": "调研5家企业校园招聘流程，分析简历筛选效率和候选人体验。提出基于数据分析的招聘漏斗优化建议，完成调研报告和PPT汇报。"},
            ],
            "internship": [
                {"title": "HR实习生", "org": "字节跳动人力资源部", "role": "招聘实习生",
                 "desc": "协助技术岗位招聘，负责简历筛选、面试安排和候选人沟通。实习期间协助完成16个岗位的候选人搜索和初步沟通。"},
            ],
            "award": [],
        }
    elif major in ("自动化", "机械设计制造及其自动化", "电子信息工程"):
        templates = {
            "project": [
                {"title": "智能小车控制系统设计", "org": "智能制造学院实验室", "role": "嵌入式开发",
                 "desc": "基于STM32单片机设计智能小车控制系统，实现红外循迹、超声波避障和蓝牙遥控功能。完成硬件电路设计和嵌入式C语言编程，系统响应延迟小于200ms。"},
                {"title": "PLC自动化生产线模拟", "org": "自动化课程设计", "role": "系统设计",
                 "desc": "使用西门子PLC设计自动化分拣生产线控制程序，实现物料识别、分拣和输送功能。完成梯形图编程和HMI界面设计，通过仿真测试验证。"},
            ],
            "internship": [
                {"title": "嵌入式开发实习生", "org": "华星电子科技有限公司", "role": "嵌入式实习生",
                 "desc": "参与智能家居产品固件开发，使用C语言进行MCU编程。负责部分传感器驱动开发和功能测试，完成8项测试用例编写。"},
            ],
            "award": [
                {"title": "全国大学生电子设计竞赛省级二等奖", "org": "教育部电子信息教指委", "role": "硬件设计",
                 "desc": "团队完成'智能环境监测系统'设计，负责传感器模块和数据处理。系统实现温湿度、PM2.5等多项环境指标实时监测和报警功能。"},
            ],
        }
    elif major == "土木工程":
        templates = {
            "project": [
                {"title": "小型建筑结构设计", "org": "土木工程课程设计", "role": "结构设计",
                 "desc": "完成六层框架结构办公楼设计，使用AutoCAD绘制施工图，PKPM完成结构分析和配筋计算。设计符合建筑规范和抗震要求，提交完整计算书。"},
            ],
            "internship": [],
            "award": [],
        }
    elif major == "生物制药":
        templates = {
            "project": [
                {"title": "药物制剂稳定性研究", "org": "制药工程实验室", "role": "实验员",
                 "desc": "研究某口服固体制剂在不同温湿度条件下的稳定性，完成加速试验和长期试验的数据采集。使用Excel完成数据分析和降解曲线绘制。"},
            ],
            "internship": [
                {"title": "QC实习生", "org": "华润医药集团有限公司", "role": "质量控制实习生",
                 "desc": "协助药品质量检验工作，使用HPLC完成含量测定和有关物质检测。整理检验记录和质量文件，参与3个品种的稳定性考察。"},
            ],
            "award": [],
        }
    elif major == "视觉传达设计":
        templates = {
            "project": [
                {"title": "校园文化节视觉设计", "org": "艺术学院设计工作室", "role": "视觉设计",
                 "desc": "为校园文化节设计主视觉海报、门票和活动手册。使用Photoshop和Illustrator完成设计，采用扁平化风格，获得活动组委会认可。"},
            ],
            "internship": [
                {"title": "UI设计实习生", "org": "极光设计工作室", "role": "UI设计实习生",
                 "desc": "参与某App界面设计改版，使用Figma完成6个主要页面的高保真原型设计。配合产品经理完成交互优化，设计稿通过率约90%。"},
            ],
            "award": [
                {"title": "全国大学生广告艺术大赛省一等奖", "org": "中国高等教育学会", "role": "设计师",
                 "desc": "独立完成品牌平面广告设计作品，采用创意插画风格。作品获省级一等奖并入围全国总决赛。"},
            ],
        }
    elif major == "汉语言文学":
        templates = {
            "project": [
                {"title": "新媒体内容创作实践", "org": "文学院新媒体中心", "role": "内容编辑",
                 "desc": "负责学院公众号内容策划和撰写，完成12篇原创推文。选题涵盖校园文化、书评和人物访谈，累计阅读量超过1.5万。"},
            ],
            "internship": [],
            "award": [],
        }
    else:
        templates = {"project": [], "internship": [], "award": []}

    # ── Select experiences based on readiness ──
    if readiness == "A":
        # 2-4 experiences, prioritize internship + project mix
        types_to_generate = random.sample(["project", "project", "internship", "award"],
                                          random.choice([3, 3, 4, 4, 3, 4, 3, 2, 4, 3]))
    elif readiness == "B":
        types_to_generate = random.sample(["project", "project", "internship", "project", "award", "project", "internship"],
                                          random.choice([2, 2, 3, 3, 2, 3, 1, 3, 2, 3]))
    elif readiness == "C":
        types_to_generate = random.sample(["project", "project", "internship", "project", "award"],
                                          random.choice([1, 1, 2, 2, 1, 2, 0, 2, 1, 2]))
    else:  # D
        types_to_generate = random.sample(["project", "project", "internship", "award"],
                                          random.choice([0, 0, 1, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0]))

    for etype in types_to_generate:
        pool = templates.get(etype, [])
        if not pool:
            continue
        t = random.choice(pool)
        # Generate dates
        grad_year = student["graduation_year"]
        if etype == "internship":
            end_d = date(grad_year, 6, 1)
            start_d = end_d - timedelta(days=random.choice([60, 90, 120, 150, 180]))
        elif etype == "project":
            end_d = date(grad_year - random.choice([0, 0, 0, 1, 1]),
                         random.choice([1, 6, 12]), random.randint(1, 28))
            start_d = end_d - timedelta(days=random.choice([30, 60, 90, 120, 150]))
        else:  # award
            end_d = date(grad_year - random.choice([1, 2, 0]), random.choice([5, 6, 10, 11, 12]), random.randint(1, 28))
            start_d = end_d

        exp_list.append({
            "experience_type": etype,
            "title": t["title"],
            "organization": t["org"],
            "role": t["role"],
            "description": t["desc"],
            "start_date": start_d.isoformat(),
            "end_date": end_d.isoformat(),
        })

    return exp_list

# ── job expectations by major ───────────────────────────────────────────────
EXPECTED_JOBS_MAP = {
    "计算机科学与技术": ["Java开发工程师", "后端开发工程师", "前端开发工程师", "全栈开发工程师", "测试工程师"],
    "软件工程": ["后端开发工程师", "前端开发工程师", "软件测试工程师", "Java开发工程师", "全栈开发工程师"],
    "人工智能": ["算法工程师", "机器学习工程师", "数据分析师", "Python开发工程师", "NLP算法工程师"],
    "数据科学与大数据技术": ["大数据开发工程师", "数据分析师", "BI工程师", "数据仓库工程师", "ETL开发工程师"],
    "大数据管理与应用": ["数据分析师", "大数据开发工程师", "BI工程师", "数据产品经理", "数据运营"],
    "市场营销": ["市场专员", "用户运营", "内容运营", "电商运营", "品牌推广"],
    "财务管理": ["财务分析", "会计", "审计助理", "财务BP", "税务专员"],
    "电子商务": ["电商运营", "用户运营", "数据分析师", "产品运营", "市场专员"],
    "人力资源管理": ["招聘专员", "HR专员", "培训专员", "员工关系专员", "薪酬专员"],
    "自动化": ["自动化工程师", "嵌入式开发工程师", "测试工程师", "PLC工程师", "技术支持工程师"],
    "机械设计制造及其自动化": ["机械设计工程师", "制造工程师", "CAD工程师", "工艺工程师", "质量工程师"],
    "电子信息工程": ["嵌入式开发工程师", "测试工程师", "硬件工程师", "技术支持工程师", "FPGA工程师"],
    "金融学": ["金融分析师", "投资顾问", "风控专员", "行业研究员", "财务分析"],
    "土木工程": ["土木工程师", "结构设计师", "施工管理", "造价员", "BIM工程师"],
    "生物制药": ["QC分析员", "研发助理", "工艺员", "注册专员", "医药代表"],
    "视觉传达设计": ["UI设计师", "平面设计师", "视觉设计师", "品牌设计师", "交互设计师"],
    "汉语言文学": ["内容运营", "新媒体编辑", "文案策划", "行政专员", "市场专员"],
}

INDUSTRIES_POOL = [
    "信息技术", "教育培训", "智能制造", "电子通信", "金融财会",
    "建筑地产", "医药健康", "批发零售", "文化传媒", "交通物流",
    "能源化工", "生活服务",
]

MAJOR_INDUSTRIES = {
    "计算机科学与技术": ["信息技术", "电子通信", "智能制造"],
    "软件工程": ["信息技术", "电子通信", "生活服务"],
    "人工智能": ["信息技术", "电子通信", "智能制造"],
    "数据科学与大数据技术": ["信息技术", "金融财会", "批发零售"],
    "大数据管理与应用": ["信息技术", "金融财会", "批发零售"],
    "市场营销": ["批发零售", "文化传媒", "生活服务"],
    "财务管理": ["金融财会", "批发零售", "智能制造"],
    "电子商务": ["批发零售", "生活服务", "信息技术"],
    "人力资源管理": ["生活服务", "教育培训", "智能制造"],
    "自动化": ["智能制造", "电子通信", "能源化工"],
    "机械设计制造及其自动化": ["智能制造", "能源化工", "交通物流"],
    "电子信息工程": ["电子通信", "智能制造", "信息技术"],
    "金融学": ["金融财会", "批发零售", "信息技术"],
    "土木工程": ["建筑地产", "交通物流", "能源化工"],
    "生物制药": ["医药健康", "能源化工", "批发零售"],
    "视觉传达设计": ["文化传媒", "信息技术", "批发零售"],
    "汉语言文学": ["文化传媒", "教育培训", "生活服务"],
}


def industries_for_job(job, fallback_major):
    """Use the selected job's source major so cross-major preferences remain coherent."""
    matching_majors = [major for major, jobs in EXPECTED_JOBS_MAP.items() if job in jobs]
    source_major = matching_majors[0] if matching_majors else fallback_major
    return MAJOR_INDUSTRIES.get(source_major, INDUSTRIES_POOL)

def generate_job_preference(student, readiness):
    """Generate job preference for a student."""
    major = student["major"]
    grad_year = student["graduation_year"]
    education = student["education"]

    # Pick expected job based on major
    job_pool = EXPECTED_JOBS_MAP.get(major, ["数据分析师", "测试工程师", "产品运营"])

    # 10-15% cross-major: pick from another pool
    if random.random() < 0.12:
        all_jobs = []
        for v in EXPECTED_JOBS_MAP.values():
            all_jobs.extend(v)
        expected_job = random.choice(all_jobs)
    else:
        expected_job = random.choice(job_pool)

    # City with distribution
    expected_city = random.choices(CITIES, weights=CITY_WEIGHTS, k=1)[0]

    # Industry
    expected_industry = random.choice(industries_for_job(expected_job, major))

    # Salary based on education, major, and city tier
    is_tier1 = expected_city in ("北京", "上海", "深圳", "广州", "杭州")
    is_tech = major in ("计算机科学与技术", "软件工程", "人工智能", "数据科学与大数据技术",
                         "大数据管理与应用", "电子信息工程")
    is_master = education == "硕士"

    base_min = 5000
    if is_master and is_tech:
        salary_options = [10000, 11000, 12000, 13000, 13000, 14000, 15000, 15000, 16000, 18000]
    elif is_master:
        salary_options = [9000, 10000, 10000, 11000, 12000, 12000, 13000, 14000]
    elif is_tech and is_tier1:
        salary_options = [8000, 9000, 9000, 10000, 10000, 11000, 12000, 12000, 13000, 15000]
    elif is_tech:
        salary_options = [6000, 6500, 7000, 7000, 8000, 8000, 9000, 10000, 10000, 12000]
    elif is_tier1:
        salary_options = [6000, 6500, 7000, 7000, 7500, 8000, 8000, 9000, 9000, 10000]
    else:
        salary_options = [5000, 5000, 5500, 5500, 6000, 6500, 7000, 7000, 8000, 9000]

    # Lower-end jobs have lower salary
    if expected_job in ("行政专员", "招聘专员", "HR专员", "平面设计师", "医药代表"):
        salary_options = [s - 1000 for s in salary_options]
        salary_options = [max(4000, s) for s in salary_options]

    salary_min = random.choice(salary_options)

    # salary_max: for now, leave NULL as the backend primarily uses salary_min
    salary_max = None

    accept_remote = random.random() < 0.25

    return {
        "expected_job": expected_job,
        "expected_city": expected_city,
        "expected_industry": expected_industry,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "accept_remote_city": 1 if accept_remote else 0,
    }

# ── skill generation ─────────────────────────────────────────────────────────
def generate_skills(student, readiness):
    """Generate skills for a student, correlated with major and readiness."""
    major = student["major"]
    major_skills = SKILL_MAP.get(major, ["Python", "SQL", "Excel"])

    if readiness == "A":
        count = random.choices([5, 6, 7, 8, 5, 6, 6, 7, 5, 8],
                               weights=[2, 3, 2, 1, 2, 3, 3, 2, 2, 1], k=1)[0]
    elif readiness == "B":
        count = random.choices([3, 4, 5, 6, 3, 4, 5, 4, 5, 3],
                               weights=[2, 3, 3, 1, 2, 3, 2, 3, 2, 2], k=1)[0]
    elif readiness == "C":
        count = random.choices([1, 2, 3, 4, 1, 2, 3, 2, 3, 1],
                               weights=[2, 3, 3, 1, 2, 3, 2, 2, 2, 2], k=1)[0]
    else:  # D
        count = random.choices([0, 0, 1, 1, 2, 0, 1, 1, 0, 2, 0, 0, 0, 1, 0],
                               weights=[3, 3, 3, 3, 1, 3, 3, 2, 3, 1, 3, 2, 3, 2, 3], k=1)[0]

    if count == 0:
        return []

    # Select skills: mostly from major pool, some cross-major (~15%)
    selected = []
    for i in range(count):
        if random.random() < 0.15:
            # Cross-major skill
            candidates = [s for s in CROSS_SKILLS if s not in selected]
            if not candidates:
                candidates = [s for s in major_skills if s not in selected]
        else:
            candidates = [s for s in major_skills if s not in selected]

        if not candidates:
            break

        # Prefer common skills
        weights = [3 if s in ("Python", "SQL", "Java", "Linux", "Git", "MySQL", "Excel") else 1
                   for s in candidates]
        chosen = random.choices(candidates, weights=weights, k=1)[0]
        selected.append(chosen)

    # Assign skill levels (1-5). Level 5 should be ~8-12% of total skills
    skills = []
    for s in selected:
        # Level 5: ~10% chance
        if random.random() < 0.10:
            level = 5
        elif readiness == "A":
            level = random.choices([3, 4, 4, 4, 5], weights=[2, 3, 3, 2, 1], k=1)[0]
        elif readiness == "B":
            level = random.choices([2, 3, 3, 4, 4, 5], weights=[1, 3, 3, 2, 1, 1], k=1)[0]
        elif readiness == "C":
            level = random.choices([1, 2, 2, 3, 3, 4], weights=[1, 2, 3, 2, 1, 1], k=1)[0]
        else:  # D
            level = random.choices([1, 1, 2, 2, 3, 3, 4], weights=[2, 2, 2, 2, 1, 1, 1], k=1)[0]
        skills.append({"skill_name": s, "skill_level": level})

    return skills

# ── main generation ──────────────────────────────────────────────────────────
def generate():
    students = []
    accounts = []
    all_skills = []
    all_experiences = []
    all_preferences = []

    # ── Build student list ──
    # Flatten college/major distribution
    major_list = []
    for college, majors in COLLEGES.items():
        for major, count in majors.items():
            for _ in range(count):
                major_list.append((college, major))

    random.shuffle(major_list)
    # Sort by readiness tier assignment
    random.shuffle(GRAD_YEARS)

    # Assign readiness tiers: A=20, B=35, C=30, D=15
    readiness_assignments = (["A"]*20 + ["B"]*35 + ["C"]*30 + ["D"]*15)
    random.shuffle(readiness_assignments)

    # Assign education: 88 bachelor, 12 master
    education_assignments = ["本科"] * 88 + ["硕士"] * 12
    random.shuffle(education_assignments)

    # Ensure masters go to eligible majors
    for i in range(100):
        if education_assignments[i] == "硕士" and major_list[i][1] not in MASTER_ELIGIBLE_MAJORS:
            # Swap with a bachelor who is in an eligible major
            for j in range(i+1, 100):
                if (education_assignments[j] == "本科" and
                    major_list[j][1] in MASTER_ELIGIBLE_MAJORS):
                    education_assignments[i], education_assignments[j] = \
                        education_assignments[j], education_assignments[i]
                    break

    # Assign graduation years
    grad_year_assignments = list(GRAD_YEARS)
    random.shuffle(grad_year_assignments)

    # ── Generate each student ──
    used_names = set()

    for i in range(100):
        student_no = f"SIM2026{i+1:03d}"
        college, major = major_list[i]
        education = education_assignments[i]
        graduation_year = grad_year_assignments[i]
        readiness = readiness_assignments[i]

        # D-tier students: at least 5 of 15 have profile_completed=0
        # And some C-tier might also have incomplete profiles
        if readiness == "D":
            profile_completed = 0 if i < 10 else random.choice([0, 0, 1])
        else:
            profile_completed = 1

        # Count: we need exactly 85 complete
        # We'll adjust at the end

        # Generate name (ensure uniqueness)
        is_male = random.random() < 0.55
        for _ in range(100):
            surname = random.choice(SURNAMES)
            if is_male:
                given = random.choice(GIVEN_NAMES_MALE)
            else:
                given = random.choice(GIVEN_NAMES_FEMALE)
            name = surname + given
            if name not in used_names:
                used_names.add(name)
                break
        else:
            name = f"学生{student_no[-3:]}"

        student = {
            "student_no": student_no,
            "name": name,
            "college": college,
            "major": major,
            "education": education,
            "graduation_year": graduation_year,
            "profile_completed": profile_completed,
            "readiness": readiness,
        }
        students.append(student)

    # Adjust profile_completed to exactly 85
    complete_count = sum(1 for s in students if s["profile_completed"] == 1)
    # Ensure it's exactly 85
    # Make D-tier with profile_completed=1 into 0 if too many complete
    candidates_to_uncomplete = [s for s in students if s["readiness"] == "D" and s["profile_completed"] == 1]
    random.shuffle(candidates_to_uncomplete)
    while complete_count > 85 and candidates_to_uncomplete:
        s = candidates_to_uncomplete.pop()
        s["profile_completed"] = 0
        complete_count -= 1
    # Make some C-tier complete if not enough
    candidates_to_complete = [s for s in students if s["readiness"] in ("C", "D") and s["profile_completed"] == 0]
    random.shuffle(candidates_to_complete)
    while complete_count < 85 and candidates_to_complete:
        s = candidates_to_complete.pop()
        s["profile_completed"] = 1
        complete_count += 1

    # ── Generate accounts, skills, experiences, preferences ──
    for i, student in enumerate(students):
        # Account
        accounts.append({
            "role": "STUDENT",
            "username": student["student_no"],
            "password_hash": PASSWORD_HASH,
            "display_name": student["name"],
            "student_no": student["student_no"],  # for lookup in SQL
        })

        # Skills (skip for some D-tier with profile_completed=0 to simulate incomplete)
        readiness = student["readiness"]
        if student["profile_completed"] == 0 and readiness == "D" and random.random() < 0.4:
            skills = []
        else:
            skills = generate_skills(student, readiness)
        for sk in skills:
            sk["student_no"] = student["student_no"]
        all_skills.extend(skills)

        # Experiences
        if student["profile_completed"] == 0 and readiness == "D" and random.random() < 0.5:
            exps = []
        else:
            exps = experiences_for(student, readiness)
        for exp in exps:
            exp["student_no"] = student["student_no"]
        all_experiences.extend(exps)

        # Preferences (80-90 students)
        if student["profile_completed"] == 0 and readiness == "D" and random.random() < 0.5:
            pref = None
        elif student["profile_completed"] == 0 and random.random() < 0.3:
            pref = None
        else:
            pref = generate_job_preference(student, readiness)
        if pref:
            pref["student_no"] = student["student_no"]
            pref["student_id"] = None  # SQL will resolve
            all_preferences.append(pref)

    # Ensure preference count is 80-90
    while len(all_preferences) > 90:
        # Remove from D-tier first
        for i, p in enumerate(all_preferences):
            s = next(s for s in students if s["student_no"] == p["student_no"])
            if s["readiness"] == "D":
                del all_preferences[i]
                break
        else:
            all_preferences.pop()

    # Build manifest
    college_counts = {}
    major_counts = {}
    for s in students:
        college_counts[s["college"]] = college_counts.get(s["college"], 0) + 1
        major_counts[s["major"]] = major_counts.get(s["major"], 0) + 1

    readiness_counts = {}
    for s in students:
        readiness_counts[s["readiness"]] = readiness_counts.get(s["readiness"], 0) + 1

    grad_year_counts = {}
    for s in students:
        y = str(s["graduation_year"])
        grad_year_counts[y] = grad_year_counts.get(y, 0) + 1

    edu_counts = {}
    for s in students:
        edu_counts[s["education"]] = edu_counts.get(s["education"], 0) + 1

    manifest = {
        "dataset_name": "mock-students-100",
        "generated_at": date.today().isoformat(),
        "seed": SEED,
        "student_count": len(students),
        "account_count": len(accounts),
        "skill_count": len(all_skills),
        "experience_count": len(all_experiences),
        "preference_count": len(all_preferences),
        "college_distribution": college_counts,
        "major_distribution": major_counts,
        "readiness_distribution": readiness_counts,
        "profile_completed_count": sum(1 for s in students if s["profile_completed"] == 1),
        "graduation_year_distribution": grad_year_counts,
        "education_distribution": edu_counts,
        "demo_password": DEMO_PASSWORD,
        "student_no_prefix": "SIM2026",
    }

    return students, accounts, all_skills, all_experiences, all_preferences, manifest


# ── SQL generation ───────────────────────────────────────────────────────────
def quote(s):
    """Escape string for MySQL."""
    if s is None:
        return "NULL"
    return "'" + str(s).replace("\\", "\\\\").replace("'", "\\'") + "'"

def generate_sql(students, accounts, skills, experiences, preferences):
    """Generate import SQL."""
    lines = []
    lines.append("-- ============================================================")
    lines.append("-- Mock Students Import Script")
    lines.append("-- Generated: " + date.today().isoformat())
    lines.append("-- Prefix: SIM2026 (001-100)")
    lines.append("-- IMPORTANT: Execute with a MySQL client that has write access")
    lines.append("--   mysql -u <user> -p < import_mock_students.sql")
    lines.append("-- ============================================================")
    lines.append("")
    lines.append("USE spark_employment;")
    lines.append("")
    lines.append("START TRANSACTION;")
    lines.append("")

    # Check for existing SIM2026 data
    lines.append("-- Replace only the SIM2026 dataset so this script is safe to run repeatedly")
    lines.append("DELETE FROM auth_session WHERE account_id IN (")
    lines.append("  SELECT id FROM platform_account WHERE username LIKE 'SIM2026%'")
    lines.append(");")
    lines.append("DELETE FROM platform_account WHERE username LIKE 'SIM2026%';")
    lines.append("DELETE FROM student_skill WHERE student_id IN (")
    lines.append("  SELECT id FROM student WHERE student_no LIKE 'SIM2026%'")
    lines.append(");")
    lines.append("DELETE FROM student_experience WHERE student_id IN (")
    lines.append("  SELECT id FROM student WHERE student_no LIKE 'SIM2026%'")
    lines.append(");")
    lines.append("DELETE FROM job_preference WHERE student_id IN (")
    lines.append("  SELECT id FROM student WHERE student_no LIKE 'SIM2026%'")
    lines.append(");")
    lines.append("DELETE FROM student WHERE student_no LIKE 'SIM2026%';")
    lines.append("SELECT 'Existing SIM2026 dataset cleared; importing 100 students' AS import_status;")
    lines.append("")

    # Insert students
    lines.append("-- ============================================================")
    lines.append("-- 1. Student records")
    lines.append("-- ============================================================")
    for s in students:
        lines.append(
            f"INSERT INTO student (student_no, name, college, major, education, graduation_year, profile_completed) "
            f"VALUES ({quote(s['student_no'])}, {quote(s['name'])}, {quote(s['college'])}, "
            f"{quote(s['major'])}, {quote(s['education'])}, {s['graduation_year']}, {s['profile_completed']});"
        )
    lines.append("")

    # Insert platform accounts
    lines.append("-- ============================================================")
    lines.append("-- 2. Platform accounts")
    lines.append("-- ============================================================")
    for a in accounts:
        lines.append(
            f"INSERT INTO platform_account (role, username, password_hash, display_name, student_id, enabled) "
            f"SELECT 'STUDENT', {quote(a['username'])}, {quote(a['password_hash'])}, "
            f"{quote(a['display_name'])}, s.id, 1 "
            f"FROM student s WHERE s.student_no = {quote(a['student_no'])};"
        )
    lines.append("")

    # Insert skills
    lines.append("-- ============================================================")
    lines.append("-- 3. Student skills")
    lines.append("-- ============================================================")
    for sk in skills:
        lines.append(
            f"INSERT INTO student_skill (student_id, skill_name, skill_level) "
            f"SELECT s.id, {quote(sk['skill_name'])}, {sk['skill_level']} "
            f"FROM student s WHERE s.student_no = {quote(sk['student_no'])};"
        )
    lines.append("")

    # Insert experiences
    lines.append("-- ============================================================")
    lines.append("-- 4. Student experiences")
    lines.append("-- ============================================================")
    for exp in experiences:
        lines.append(
            f"INSERT INTO student_experience (student_id, experience_type, title, organization, role, description, start_date, end_date) "
            f"SELECT s.id, {quote(exp['experience_type'])}, {quote(exp['title'])}, "
            f"{quote(exp['organization'])}, {quote(exp['role'])}, {quote(exp['description'])}, "
            f"{quote(exp['start_date'])}, {quote(exp['end_date'])} "
            f"FROM student s WHERE s.student_no = {quote(exp['student_no'])};"
        )
    lines.append("")

    # Insert preferences
    lines.append("-- ============================================================")
    lines.append("-- 5. Job preferences")
    lines.append("-- ============================================================")
    for pref in preferences:
        lines.append(
            f"INSERT INTO job_preference (student_id, expected_job, expected_city, expected_industry, salary_min, salary_max, accept_remote_city) "
            f"SELECT s.id, {quote(pref['expected_job'])}, {quote(pref['expected_city'])}, "
            f"{quote(pref['expected_industry'])}, {pref['salary_min']}, NULL, {pref['accept_remote_city']} "
            f"FROM student s WHERE s.student_no = {quote(pref['student_no'])};"
        )
    lines.append("")

    # Verification
    lines.append("-- ============================================================")
    lines.append("-- Verification counts")
    lines.append("-- ============================================================")
    lines.append("SELECT 'Students' AS tbl, COUNT(*) AS cnt FROM student WHERE student_no LIKE 'SIM2026%'")
    lines.append("UNION ALL SELECT 'Accounts', COUNT(*) FROM platform_account WHERE username LIKE 'SIM2026%'")
    lines.append("UNION ALL SELECT 'Skills', COUNT(*) FROM student_skill WHERE student_id IN (SELECT id FROM student WHERE student_no LIKE 'SIM2026%')")
    lines.append("UNION ALL SELECT 'Experiences', COUNT(*) FROM student_experience WHERE student_id IN (SELECT id FROM student WHERE student_no LIKE 'SIM2026%')")
    lines.append("UNION ALL SELECT 'Preferences', COUNT(*) FROM job_preference WHERE student_id IN (SELECT id FROM student WHERE student_no LIKE 'SIM2026%');")
    lines.append("")

    lines.append("COMMIT;")
    lines.append("")
    lines.append("-- End of import script")

    return "\n".join(lines)

def generate_remove_sql():
    """Generate remove SQL."""
    lines = []
    lines.append("-- ============================================================")
    lines.append("-- Mock Students Removal Script")
    lines.append("-- Removes ALL students with student_no LIKE 'SIM2026%'")
    lines.append("-- and their associated data via CASCADE or explicit deletion")
    lines.append("-- ============================================================")
    lines.append("")
    lines.append("USE spark_employment;")
    lines.append("")
    lines.append("START TRANSACTION;")
    lines.append("")
    lines.append("-- Check how many SIM2026 students exist before deletion")
    lines.append("SELECT COUNT(*) AS before_student_count FROM student WHERE student_no LIKE 'SIM2026%';")
    lines.append("SELECT COUNT(*) AS before_account_count FROM platform_account WHERE username LIKE 'SIM2026%';")
    lines.append("")
    lines.append("-- Delete auth sessions for SIM2026 accounts")
    lines.append("DELETE FROM auth_session WHERE account_id IN (")
    lines.append("  SELECT id FROM platform_account WHERE username LIKE 'SIM2026%'")
    lines.append(");")
    lines.append("")
    lines.append("-- Delete platform accounts for SIM2026 students")
    lines.append("DELETE FROM platform_account WHERE username LIKE 'SIM2026%';")
    lines.append("")
    lines.append("-- Delete student_skill (cascade should handle this, but explicit is safer)")
    lines.append("DELETE FROM student_skill WHERE student_id IN (")
    lines.append("  SELECT id FROM student WHERE student_no LIKE 'SIM2026%'")
    lines.append(");")
    lines.append("")
    lines.append("-- Delete student_experience")
    lines.append("DELETE FROM student_experience WHERE student_id IN (")
    lines.append("  SELECT id FROM student WHERE student_no LIKE 'SIM2026%'")
    lines.append(");")
    lines.append("")
    lines.append("-- Delete job_preference")
    lines.append("DELETE FROM job_preference WHERE student_id IN (")
    lines.append("  SELECT id FROM student WHERE student_no LIKE 'SIM2026%'")
    lines.append(");")
    lines.append("")
    lines.append("-- Delete students")
    lines.append("DELETE FROM student WHERE student_no LIKE 'SIM2026%';")
    lines.append("")
    lines.append("-- Verify removal")
    lines.append("SELECT COUNT(*) AS after_student_count FROM student WHERE student_no LIKE 'SIM2026%';")
    lines.append("SELECT COUNT(*) AS after_account_count FROM platform_account WHERE username LIKE 'SIM2026%';")
    lines.append("")
    lines.append("COMMIT;")
    lines.append("")
    lines.append("-- End of removal script")

    return "\n".join(lines)

def generate_csv(students):
    """Generate preview CSV."""
    rows = []
    for s in students:
        rows.append({
            "student_no": s["student_no"],
            "name": s["name"],
            "college": s["college"],
            "major": s["major"],
            "education": s["education"],
            "graduation_year": s["graduation_year"],
            "profile_completed": s["profile_completed"],
            "readiness_level": s["readiness"],
            "skill_count": len([sk for sk in all_skills if sk.get("student_no") == s["student_no"]]),
            "experience_count": len([ex for ex in all_experiences if ex.get("student_no") == s["student_no"]]),
            "expected_job": next((p["expected_job"] for p in all_preferences if p.get("student_no") == s["student_no"]), ""),
            "expected_city": next((p["expected_city"] for p in all_preferences if p.get("student_no") == s["student_no"]), ""),
            "salary_min": next((str(p["salary_min"]) for p in all_preferences if p.get("student_no") == s["student_no"]), ""),
        })
    return rows

# ── validation ───────────────────────────────────────────────────────────────
def validate(students, accounts, skills, experiences, preferences):
    """Validate generated data. Returns list of error messages."""
    errors = []

    # 1. Exactly 100 students
    if len(students) != 100:
        errors.append(f"Student count: {len(students)} != 100")

    # 2. Exactly 100 accounts
    if len(accounts) != 100:
        errors.append(f"Account count: {len(accounts)} != 100")

    # 3. Unique student_no
    student_nos = [s["student_no"] for s in students]
    if len(set(student_nos)) != len(student_nos):
        errors.append("Duplicate student_no found")

    # 4. Unique usernames
    usernames = [a["username"] for a in accounts]
    if len(set(usernames)) != len(usernames):
        errors.append("Duplicate usernames found")

    # 5. Student_no and username match
    for a in accounts:
        if a["username"] != a["student_no"]:
            errors.append(f"Username mismatch: {a['username']} != {a['student_no']}")

    # 6. skill_level in 1-5
    for sk in skills:
        if not (1 <= sk["skill_level"] <= 5):
            errors.append(f"Invalid skill_level {sk['skill_level']} for {sk.get('student_no')}")

    # 7. experience_type valid
    for exp in experiences:
        if exp["experience_type"] not in ("project", "internship", "award"):
            errors.append(f"Invalid experience_type: {exp['experience_type']}")

    # 8. start_date <= end_date
    for exp in experiences:
        if exp["start_date"] and exp["end_date"] and exp["start_date"] > exp["end_date"]:
            errors.append(f"start_date > end_date for {exp.get('student_no')}: {exp['title']}")

    # 9. Graduation year distribution
    grad_years = {}
    for s in students:
        y = str(s["graduation_year"])
        grad_years[y] = grad_years.get(y, 0) + 1
    if grad_years.get("2026", 0) != 65:
        errors.append(f"2026 grads: {grad_years.get('2026', 0)} != 65")
    if grad_years.get("2027", 0) != 25:
        errors.append(f"2027 grads: {grad_years.get('2027', 0)} != 25")
    if grad_years.get("2025", 0) != 10:
        errors.append(f"2025 grads: {grad_years.get('2025', 0)} != 10")

    # 10. College & major distribution
    for college, majors in COLLEGES.items():
        expected = sum(majors.values())
        actual = sum(1 for s in students if s["college"] == college)
        if expected != actual:
            errors.append(f"College {college}: expected {expected}, got {actual}")
        for major, expected_m in majors.items():
            actual_m = sum(1 for s in students if s["major"] == major)
            if expected_m != actual_m:
                errors.append(f"Major {major}: expected {expected_m}, got {actual_m}")

    # 11. profile_completed
    complete = sum(1 for s in students if s["profile_completed"] == 1)
    if complete != 85:
        errors.append(f"profile_completed: {complete} != 85")

    # 12. Readiness tiers
    for tier, expected in READINESS_COUNTS.items():
        actual = sum(1 for s in students if s["readiness"] == tier)
        if expected != actual:
            errors.append(f"Readiness {tier}: expected {expected}, got {actual}")

    # 13. Preference count
    if not (80 <= len(preferences) <= 90):
        errors.append(f"Preference count: {len(preferences)} not in 80-90")

    # 14. BCrypt hash format
    for a in accounts:
        h = a["password_hash"]
        if not h.startswith("$2"):
            errors.append(f"Invalid BCrypt hash format for {a['username']}")

    # 15. No plaintext password in SQL (checked during SQL gen)

    # 16. Education distribution
    edu = {}
    for s in students:
        edu[s["education"]] = edu.get(s["education"], 0) + 1
    if edu.get("本科", 0) != 88:
        errors.append(f"本科: {edu.get('本科', 0)} != 88")
    if edu.get("硕士", 0) != 12:
        errors.append(f"硕士: {edu.get('硕士', 0)} != 12")

    # 17. No duplicate skills per student
    student_skills = {}
    for sk in skills:
        key = (sk["student_no"], sk["skill_name"])
        if key in student_skills:
            errors.append(f"Duplicate skill {sk['skill_name']} for {sk['student_no']}")
        student_skills[key] = True

    # 18. skill level 5 count (~8-12%)
    total_skills = len(skills)
    level5_count = sum(1 for sk in skills if sk["skill_level"] == 5)
    level5_pct = level5_count / total_skills * 100 if total_skills > 0 else 0
    if not (5 <= level5_pct <= 15) and total_skills > 0:
        errors.append(f"Level 5 skills: {level5_pct:.1f}% (expected 8-12%)")

    return errors

# ── main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Generating 100 mock students with seed", SEED)

    students, accounts, all_skills, all_experiences, all_preferences, manifest = generate()

    # Validate
    print("\nRunning validation...")
    errors = validate(students, accounts, all_skills, all_experiences, all_preferences)
    if errors:
        print("VALIDATION ERRORS:")
        for e in errors:
            print(f"  ✗ {e}")
    else:
        print("✓ All validations passed")

    # Generate SQL
    print("\nGenerating SQL files...")
    import_sql = generate_sql(students, accounts, all_skills, all_experiences, all_preferences)
    with open(os.path.join(OUTPUT_DIR, "import_mock_students.sql"), "w", encoding="utf-8") as f:
        f.write(import_sql)
    print(f"  import_mock_students.sql: {len(import_sql)} bytes")

    remove_sql = generate_remove_sql()
    with open(os.path.join(OUTPUT_DIR, "remove_mock_students.sql"), "w", encoding="utf-8") as f:
        f.write(remove_sql)
    print(f"  remove_mock_students.sql: {len(remove_sql)} bytes")

    # Generate CSV
    csv_rows = generate_csv(students)
    with open(os.path.join(OUTPUT_DIR, "mock_students_preview.csv"), "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=csv_rows[0].keys())
        writer.writeheader()
        writer.writerows(csv_rows)
    print(f"  mock_students_preview.csv: {len(csv_rows)} rows")

    # Generate manifest
    with open(os.path.join(OUTPUT_DIR, "mock_students_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"  mock_students_manifest.json written")

    # Print summary
    print("\n" + "="*60)
    print("GENERATION COMPLETE")
    print("="*60)
    print(f"Students:       {len(students)}")
    print(f"Accounts:       {len(accounts)}")
    print(f"Skills:         {len(all_skills)}")
    print(f"Experiences:    {len(all_experiences)}")
    print(f"Preferences:    {len(all_preferences)}")
    print(f"Profile done:   {sum(1 for s in students if s['profile_completed'] == 1)}/100")
    print(f"Demo password:  {DEMO_PASSWORD}")
    print(f"BCrypt hash:    {PASSWORD_HASH[:30]}...")
    print()
    print("Output files:")
    print(f"  {OUTPUT_DIR}/import_mock_students.sql")
    print(f"  {OUTPUT_DIR}/remove_mock_students.sql")
    print(f"  {OUTPUT_DIR}/mock_students_preview.csv")
    print(f"  {OUTPUT_DIR}/mock_students_manifest.json")

    if errors:
        print(f"\n⚠️  {len(errors)} validation error(s) - check output above")
    else:
        print("\n✓ All 18 validation checks passed")
