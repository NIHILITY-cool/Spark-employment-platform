# 部署说明

## Docker Compose

复制 `.env.example` 为本地 `.env`，设置 MySQL 密码后，在项目根目录运行：

```bash
docker compose up --build
```

默认端口：

- 前端：`http://localhost:5173`
- Spring Boot API：`http://localhost:8082/api`
- MySQL：`localhost:3306`
- Redis：`localhost:6379`

虚拟机中的 Spark Master 使用 `7077`，Spark Web UI 使用 `8080`，因此 Spring Boot 固定使用 `8082`。
