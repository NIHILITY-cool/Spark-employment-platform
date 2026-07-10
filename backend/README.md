# 后端模块

## 模块职责

基于 Flask 的 RESTful API 后端，提供学生端和高校端的业务接口。

## 环境安装

```bash
cd backend
pip install -r requirements.txt
```

## 启动

```bash
python run.py
```

## 主要接口

### 认证
- `POST /api/auth/register` - 注册
- `POST /api/auth/login` - 登录

### 学生端
- `GET /api/students/profile` - 获取个人信息
- `PUT /api/students/profile` - 修改个人信息
- `GET /api/students/skills` - 获取技能
- `POST /api/students/skills` - 添加技能
- `DELETE /api/students/skills/{id}` - 删除技能
- `GET /api/students/preference` - 获取求职意愿
- `PUT /api/students/preference` - 修改求职意愿

### 岗位
- `GET /api/jobs` - 岗位搜索
- `GET /api/jobs/{job_id}` - 岗位详情
- `POST /api/jobs/{job_id}/favorite` - 收藏岗位
- `DELETE /api/jobs/{job_id}/favorite` - 取消收藏

### 推荐
- `GET /api/recommendations` - 获取推荐
- `GET /api/recommendations/{job_id}/match` - 匹配详情
- `GET /api/recommendations/skill-gap` - 技能差距

### 高校端
- `GET /api/university/overview` - 高校总览
- `GET /api/university/student-intentions` - 求职意愿统计
- `GET /api/university/student-skills` - 学生能力分析
- `GET /api/university/major-match` - 专业匹配分析
- `GET /api/university/major-skill-gap` - 专业技能差距
- `GET /api/university/market-demand` - 市场需求
- `GET /api/university/training-suggestions` - 培养建议

## 测试方法

```bash
cd backend
pytest tests/
```

## 当前负责人

待分配

## 当前进度

参见 `docs/10-progress-log.md`
