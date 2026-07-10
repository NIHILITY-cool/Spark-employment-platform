#!/bin/bash
# 运行所有测试
echo "Running tests..."
cd "$(dirname "$0")/.."
pytest data_source/tests/ 2>/dev/null
pytest data_processing/tests/ 2>/dev/null
pytest recommendation/tests/ 2>/dev/null
pytest backend/tests/ 2>/dev/null
echo "All tests completed"
