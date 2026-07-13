#!/bin/bash
# 清理 Redis 缓存
redis-cli KEYS "employment:*" | xargs redis-cli DEL 2>/dev/null
echo "Redis cache cleared"
