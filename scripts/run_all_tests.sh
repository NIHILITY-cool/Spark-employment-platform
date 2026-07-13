#!/bin/bash
set -euo pipefail

# 运行所有测试和构建检查
echo "Running tests..."
cd "$(dirname "$0")/.."
python3 -m pytest data_source/tests/ data_processing/tests/ recommendation/tests/
(cd backend && mvn test)
(cd frontend && npm run build)
echo "All tests completed"
