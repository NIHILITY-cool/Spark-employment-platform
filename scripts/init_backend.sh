#!/bin/bash
# 后端初始化脚本
cd "$(dirname "$0")/../backend"
pip install -r requirements.txt
echo "后端环境初始化完成"
