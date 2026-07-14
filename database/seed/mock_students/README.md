# Mock Students Seed Data — 100 名模拟学生

## 数据用途

为"基于 Spark 的高校智慧就业大数据分析平台"生成 100 名模拟学生及完整关联数据，用于：

- 推荐算法验证（RecommendationService）
- 高校学生情况分析（UniversityStudentInsightService）
- 前端学生端和高校端交互测试
- 多角色登录场景测试

**所有数据均为模拟数据，学号统一以 `SIM2026` 为前缀，不与真实学生混淆。**

## 数据分布

### 学院与专业（100 人）

| 学院 | 专业 | 人数 |
|------|------|------|
| 信息工程学院（30） | 计算机科学与技术 | 12 |
| | 软件工程 | 10 |
| | 人工智能 | 8 |
| 大数据学院（25） | 数据科学与大数据技术 | 15 |
| | 大数据管理与应用 | 10 |
| 经济管理学院（20） | 市场营销 | 6 |
| | 财务管理 | 6 |
| | 电子商务 | 5 |
| | 人力资源管理 | 3 |
| 智能制造学院（15） | 自动化 | 6 |
| | 机械设计制造及其自动化 | 5 |
| | 电子信息工程 | 4 |
| 其他学院（10） | 金融学 | 3 |
| | 土木工程 | 2 |
| | 生物制药 | 2 |
| | 视觉传达设计 | 2 |
| | 汉语言文学 | 1 |

### 学历

- 本科：88 人
- 硕士：12 人（集中在 AI、数据科学、计算机、软件工程、金融学）

### 毕业年份

- 2026 年：65 人
- 2027 年：25 人
- 2025 年：10 人

### 能力层次

| 层次 | 人数 | 说明 |
|------|------|------|
| A（准备充分） | 20 | 5-8 项技能，2-4 条经历，至少一段实习 |
| B（准备良好） | 35 | 3-6 项技能，1-3 条经历 |
| C（准备一般） | 30 | 1-4 项技能，0-2 条经历 |
| D（需重点关注） | 15 | 0-2 项技能，0-1 条经历，画像不完整 |

### 画像完整度

- 完整画像（profile_completed=1）：85 人
- 未完整画像（profile_completed=0）：15 人

## 默认演示密码

所有模拟学生账号初始密码统一为：

```
Student@123
```

**⚠️ 该密码仅用于本地演示和开发环境，禁止用于生产环境。**

密码以 BCrypt 哈希存储（`$2b$10$...`），由 Spring Security BCryptPasswordEncoder 兼容。

## 账号规则

- 用户名 = 学号（如 `SIM2026001` ～ `SIM2026100`）
- 角色：STUDENT
- 每个学生一个登录账号
- 不影响已有 admin、university 和真实学生账号

## 执行方法

### 1. 安装依赖（如需重新生成）

```bash
cd database/seed/mock_students
pip install -r requirements.txt
python3 generate_mock_students.py
```

### 2. 导入数据到 MySQL

```bash
mysql -u <user> -p < database/seed/mock_students/import_mock_students.sql
```

在虚拟机上执行（示例）：

```bash
source ~/employment-platform/mysql.env
mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" -h 127.0.0.1 < import_mock_students.sql
```

**重复执行安全：脚本会在同一事务中仅替换已有 SIM2026 数据，不影响其他学生。**

如果需要先删除项目此前手工录入的学生和 `demo001`，执行：

```bash
mysql -u <user> -p < database/seed/mock_students/remove_existing_demo.sql
```

该脚本只删除非 `SIM2026` 学生，导入后再次运行也不会删除新生成的 100 人。

### 3. 删除模拟数据

```bash
mysql -u <user> -p < database/seed/mock_students/remove_mock_students.sql
```

## 生成文件清单

| 文件 | 说明 |
|------|------|
| `README.md` | 本文件 |
| `generate_mock_students.py` | 可复现生成脚本（随机种子 20260714） |
| `requirements.txt` | Python 依赖 |
| `import_mock_students.sql` | MySQL 导入脚本（事务，按外键顺序） |
| `remove_mock_students.sql` | MySQL 清理脚本（只删除 SIM2026% 前缀） |
| `mock_students_preview.csv` | 人工检查用预览（100 行） |
| `mock_students_manifest.json` | 数据清单 |

## 安全警告

- 所有数据均为模拟数据
- 密码仅用于本地演示
- 不在仓库中保存数据库密码
- 不直接连接生产数据库
- 生成脚本默认只输出文件，不自动执行导入
- 删除脚本只匹配 `student_no LIKE 'SIM2026%'`，不影响其他数据
- SQL 使用事务，插入失败自动回滚

## 模拟数据边界

- 不包含真实身份证号、手机号、家庭住址等隐私信息
- 不伪造政治面貌、民族等系统不需要的字段
- 不修改 student 表结构
- 不修改 admin 和 university 账号
- D 类学生通过信息缺失和能力证据不足让系统自然判断，不填写负面或侮辱性内容
- 岗位推荐和高校分析均基于真实数据库中的 12,000 条岗位数据
- 匹配分数仅反映当前有效岗位的实时计算，不作为就业结果预测

## 验证结果

生成脚本内置 18 项验证：

1. student 恰好 100 条 ✓
2. platform_account 恰好 100 条 ✓
3. 学号和用户名唯一 ✓
4. 每个账号关联一个学生 ✓
5. 无孤立技能、经历和就业期望 ✓
6. skill_level 全部在 1-5 ✓
7. experience_type 仅 project/internship/award ✓
8. start_date ≤ end_date ✓
9. 毕业年份分布准确（65/25/10） ✓
10. 学院和专业分布准确 ✓
11. profile_completed 恰好 85 人 ✓
12. 四类准备层次 20/35/30/15 ✓
13. 就业期望 80-90 人 ✓
14. BCrypt 哈希格式正确 ✓
15. SQL 中无明文密码 ✓
16. 清理脚本仅匹配 SIM2026 前缀 ✓
17. 未修改项目页面代码 ✓
18. 未修改数据库结构 ✓
