# 数据存储与基础设施模块

## 模块职责

负责虚拟机配置、Hadoop/HDFS/Hive 环境搭建、数据目录管理和数据上传下载流程。

## 环境

- Ubuntu Server 24.04
- OpenJDK 17
- Hadoop 3.5.0
- Spark 3.5.x
- Hive 4.x（可选）

## HDFS 目录结构

```
/employment-platform/
├── raw/          # 原始数据层
├── cleaned/      # 清洗数据层
├── warehouse/    # 数据仓库（ods/dwd/dws/ads）
└── output/       # 结果输出
```

## 运行命令

```bash
# 安装 Java
bash scripts/install_java.sh

# 初始化 HDFS 目录
bash scripts/init_hdfs_dirs.sh

# 启动大数据服务
bash scripts/start_bigdata.sh

# 停止大数据服务
bash scripts/stop_bigdata.sh

# 检查服务状态
bash scripts/check_services.sh

# 上传数据到 HDFS
bash scripts/upload_to_hdfs.sh
```

## 配置说明

- `hadoop/core-site.xml.example` - HDFS 核心配置
- `hadoop/hdfs-site.xml.example` - HDFS 站点配置
- `hadoop/yarn-site.xml.example` - YARN 配置
- `hive/hive-site.xml.example` - Hive 配置

## 当前负责人

待分配

## 当前进度

参见 `docs/10-progress-log.md`
