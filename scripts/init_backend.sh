#!/bin/bash
# 后端初始化脚本 (Spring Boot + Maven)
cd "$(dirname "$0")/../backend"
mvn install -DskipTests
echo "后端环境初始化完成"
