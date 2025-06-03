# Docker 部署指南

本文档详细说明如何使用Docker部署API密钥管理系统。

## 目录

1. [快速开始](#快速开始)
2. [部署脚本](#部署脚本)
3. [详细配置](#详细配置)
4. [常见问题](#常见问题)

## 快速开始

### 前置要求

- Docker (20.10.0+)
- Docker Compose (v2.0.0+)
- Git

### 基本部署步骤

1. 克隆项目
```bash
git clone https://github.com/yourusername/api-key-manager.git
cd api-key-manager
```

2. 准备环境配置
```bash
cp .env.example .env
# 编辑.env文件，设置必要的环境变量
```

3. 生成SSL证书
```bash
./scripts/generate_ssl_cert.sh your-domain.com
```

4. 启动服务
```bash
./scripts/docker-manage.sh start
```

## 部署脚本

项目提供了两个辅助脚本来简化部署和管理过程：

### 1. SSL证书生成脚本 (generate_ssl_cert.sh)

用于生成自签名SSL证书：

```bash
./scripts/generate_ssl_cert.sh [域名]
```

- 如果不指定域名，默认使用localhost
- 证书将保存在./ssl目录下
- 生成的文件：
  - server.key：私钥
  - server.crt：证书文件

### 2. Docker管理脚本 (docker-manage.sh)

提供常用的Docker操作命令：

```bash
./scripts/docker-manage.sh [命令] [参数]
```

可用命令：
- `start`：启动所有服务
- `stop`：停止所有服务
- `restart`：重启所有服务
- `rebuild`：重新构建并启动服务
- `logs [服务]`：查看服务日志
- `status`：查看服务状态
- `backup`：备份数据库
- `restore [文件]`：恢复数据库
- `shell [服务]`：进入服务容器的shell
- `clean`：清理未使用的Docker资源
- `update`：更新应用

示例：
```bash
# 启动服务
./scripts/docker-manage.sh start

# 查看web服务日志
./scripts/docker-manage.sh logs web

# 备份数据库
./scripts/docker-manage.sh backup

# 进入web容器
./scripts/docker-manage.sh shell web
```

## 详细配置

### 环境变量配置

编辑.env文件，配置以下必要参数：

```bash
# 数据库配置
DB_PASSWORD=your_secure_password_here

# 应用配置
SECRET_KEY=your_secret_key_here

# API提供商配置
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### 服务配置

1. PostgreSQL配置
- 位置：docker-compose.yml中的db服务
- 主要参数：
  - POSTGRES_USER
  - POSTGRES_PASSWORD
  - POSTGRES_DB

2. Redis配置
- 位置：docker-compose.yml中的redis服务
- 默认使用Redis 6-alpine版本
- 数据持久化已配置

3. Nginx配置
- 配置文件：nginx.conf
- SSL证书位置：./ssl/
- 静态文件位置：./static/

## 常见问题

### 1. 服务无法启动

检查步骤：
1. 确认Docker服务正在运行
```bash
systemctl status docker
```

2. 检查服务日志
```bash
./scripts/docker-manage.sh logs
```

3. 验证端口是否被占用
```bash
netstat -tulpn | grep -E '80|443|5432|6379'
```

### 2. 数据库连接失败

检查步骤：
1. 确认数据库容器运行状态
```bash
./scripts/docker-manage.sh status
```

2. 检查数据库日志
```bash
./scripts/docker-manage.sh logs db
```

3. 验证数据库连接信息
- 检查.env文件中的DATABASE_URL配置
- 确认DB_PASSWORD设置正确

### 3. SSL证书问题

如果浏览器显示证书警告：
1. 对于开发环境，可以在浏览器中添加例外
2. 对于生产环境，建议使用Let's Encrypt获取免费的SSL证书

### 4. 性能优化

1. 调整Docker资源限制
```yaml
# 在docker-compose.yml中添加资源限制
services:
  web:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
```

2. 优化Nginx配置
- 调整worker_processes
- 配置缓存
- 启用gzip压缩

3. 优化PostgreSQL配置
- 调整shared_buffers
- 配置work_mem
- 设置effective_cache_size

### 5. 备份和恢复

1. 自动备份设置
```bash
# 添加到crontab
0 2 * * * /path/to/scripts/docker-manage.sh backup
```

2. 手动备份和恢复
```bash
# 备份
./scripts/docker-manage.sh backup

# 恢复
./scripts/docker-manage.sh restore backups/db_backup_20240120.sql
```

如需更多帮助，请查看项目文档或提交Issue。