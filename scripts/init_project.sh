#!/bin/bash
# 项目初始化脚本
echo "=== Spark 就业大数据分析平台 ==="
echo "初始化项目..."
pip install -r data_source/requirements.txt 2>/dev/null
pip install -r data_processing/requirements.txt 2>/dev/null
echo "初始化前端..."
cd frontend && npm install 2>/dev/null
echo "后端（Spring Boot Maven）请手动执行: cd backend && mvn install"
echo "初始化完成"
