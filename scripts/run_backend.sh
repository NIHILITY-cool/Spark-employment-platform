#!/bin/bash
# 启动后端服务 (Spring Boot)
cd "$(dirname "$0")/../backend"
mvn spring-boot:run
