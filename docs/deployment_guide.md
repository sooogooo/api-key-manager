# API密钥管理系统部署指南和使用手册

## 目录

- [系统要求](#系统要求)
- [部署步骤](#部署步骤)
- [配置说明](#配置说明)
- [使用指南](#使用指南)
- [常见问题](#常见问题)
- [维护指南](#维护指南)

## 系统要求

### 软件要求

- Python 3.8+
- PostgreSQL 12+（推荐）或 MySQL 8.0+
- Redis 6.0+（可选，用于缓存）
- Nginx（生产环境推荐）

### 硬件推荐配置

- CPU: 2核心及以上
- 内存: 4GB及以上
- 磁盘空间: 20GB及以上

### 操作系统支持

- Linux（推荐 Ubuntu 20.04 LTS 或 CentOS 8）
- macOS
- Windows Server 2019+

## 部署步骤

### 1. Docker部署（推荐）

使用Docker部署可以快速搭建完整的运行环境，包括应用服务器、数据库、Redis和Nginx。

#### 前置要求

1. 安装Docker和Docker Compose
```bash
# 安装Docker（Ubuntu示例）
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 部署步骤

1. 准备环境
```bash
# 克隆项目
git clone https://github.com/yourusername/api-key-manager.git
cd api-key-manager

# 复制环境配置文件
cp .env.example .env

# 编辑配置文件
nano .env
```

2. 生成SSL证书（开发环境）
```bash
# 创建ssl目录
mkdir ssl

# 生成自签名证书
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/server.key \
  -out ssl/server.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

3. 启动服务
```bash
# 构建并启动所有服务
docker-compose up --build -d

# 执行数据库迁移
docker-compose exec web flask db upgrade

# 创建管理员账户
docker-compose exec web flask create-admin
```

4. 验证部署
```bash
# 检查服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

#### 维护操作

1. 更新应用
```bash
# 拉取最新代码
git pull

# 重新构建并启动服务
docker-compose up --build -d
```

2. 数据备份
```bash
# 备份数据库
docker-compose exec db pg_dump -U aiproxy ai_proxy > backups/db_backup_$(date +%Y%m%d).sql

# 恢复数据库
cat backups/db_backup_20240120.sql | docker-compose exec -T db psql -U aiproxy ai_proxy
```

3. 查看日志
```bash
# 查看特定服务日志
docker-compose logs web
docker-compose logs nginx
docker-compose logs db
```

4. 服务管理
```bash
# 停止所有服务
docker-compose down

# 重启特定服务
docker-compose restart web

# 查看容器资源使用情况
docker stats
```

#### 故障排除

1. 容器无法启动
```bash
# 检查容器状态和日志
docker-compose ps
docker-compose logs web
```

2. 数据库连接问题
```bash
# 检查数据库日志
docker-compose logs db

# 验证数据库连接
docker-compose exec web python -c "from app import db; db.engine.connect()"
```

3. Nginx配置问题
```bash
# 测试Nginx配置
docker-compose exec nginx nginx -t

# 重新加载Nginx配置
docker-compose exec nginx nginx -s reload
```

### 2. 传统部署

如果你不想使用Docker，也可以采用传统的部署方式。

#### 准备环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Linux/macOS
source venv/bin/activate
# Windows
.\venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 数据库配置

```bash
# PostgreSQL
createdb ai_proxy
psql ai_proxy

# 创建数据库用户（在PostgreSQL命令行中）
CREATE USER aiproxy WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE ai_proxy TO aiproxy;
```

### 3. 环境变量配置

创建 `.env` 文件：

```ini
# 数据库配置
DATABASE_URL=postgresql://aiproxy:your_password@localhost/ai_proxy

# 应用配置
SECRET_KEY=your-secret-key-here
FLASK_ENV=production
FLASK_APP=app.py

# Redis配置（可选）
REDIS_URL=redis://localhost:6379/0

# API提供商配置
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
GOOGLE_API_KEY=your-google-api-key

# 安全配置
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
ADMIN_EMAIL=admin@your-domain.com
```

### 4. 初始化数据库

```bash
# 创建数据库表
flask db upgrade

# 创建管理员用户
flask create-admin
```

### 5. 生产环境配置

#### Nginx配置

创建 `/etc/nginx/sites-available/ai-proxy`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/your/static/files;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
}
```

启用站点：

```bash
ln -s /etc/nginx/sites-available/ai-proxy /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

#### Supervisor配置

创建 `/etc/supervisor/conf.d/ai-proxy.conf`:

```ini
[program:ai-proxy]
directory=/path/to/your/app
command=/path/to/your/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/ai-proxy/err.log
stdout_logfile=/var/log/ai-proxy/out.log
environment=
    DATABASE_URL="postgresql://aiproxy:your_password@localhost/ai_proxy",
    SECRET_KEY="your-secret-key-here",
    FLASK_ENV="production"
```

启动服务：

```bash
supervisorctl reread
supervisorctl update
supervisorctl start ai-proxy
```

### 6. SSL配置（推荐）

使用 Let's Encrypt：

```bash
apt install certbot python3-certbot-nginx
certbot --nginx -d your-domain.com
```

## 配置说明

### 主要配置文件

1. `config.py` - 应用配置
```python
class Config:
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 安全配置
    SECRET_KEY = os.getenv('SECRET_KEY')
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    
    # API限制配置
    DEFAULT_RATE_LIMIT = 1000  # 默认每日限制
    MAX_TOKEN_AGE = 365  # 最大令牌有效期（天）
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
```

2. `.env` - 环境变量（见上文）

### 关键参数说明

1. 数据库参数
   - `SQLALCHEMY_DATABASE_URI`: 数据库连接URL
   - `SQLALCHEMY_POOL_SIZE`: 连接池大小
   - `SQLALCHEMY_POOL_TIMEOUT`: 连接超时时间

2. 安全参数
   - `SECRET_KEY`: 用于会话加密
   - `SESSION_COOKIE_SECURE`: 仅通过HTTPS发送cookie
   - `ALLOWED_HOSTS`: 允许的域名列表

3. API限制参数
   - `DEFAULT_RATE_LIMIT`: 默认API调用限制
   - `MAX_TOKEN_AGE`: 令牌最大有效期
   - `RATE_LIMIT_WINDOW`: 限制窗口期（秒）

## 使用指南

### 管理员操作

1. 登录系统
   - 访问 `https://your-domain.com/admin`
   - 使用管理员账号登录

2. API密钥管理
   - 创建新密钥
     1. 点击"创建新密钥"按钮
     2. 填写密钥名称
     3. 设置有效期和使用限制
     4. 点击"创建"按钮
   
   - 管理现有密钥
     1. 在密钥列表中查看所有密钥
     2. 使用操作按钮启用/禁用密钥
     3. 点击密钥名称查看详情
     4. 使用删除按钮移除不需要的密钥

3. 查看统计信息
   - 访问"使用统计"页面
   - 使用过滤器选择时间范围和提供商
   - 查看图表和详细数据

4. 系统日志查看
   - 访问"系统日志"页面
   - 使用过滤器筛选日志
   - 查看详细的错误信息

### API使用说明

1. 认证方式
```http
Authorization: Bearer your-api-key
```

2. 请求示例
```bash
curl -X POST "https://your-domain.com/v1/chat/completions" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

3. 错误处理
   - 401: 未授权或密钥无效
   - 403: 超出使用限制
   - 429: 请求过于频繁
   - 500: 服务器内部错误

## 常见问题

### 1. 密钥相关

Q: 如何处理过期的密钥？
A: 系统会自动禁用过期的密钥。管理员可以在密钥列表中查看并手动处理。

Q: 如何修改密钥的使用限制？
A: 在密钥详情页面中可以修改每日使用限制。修改后立即生效。

### 2. 性能相关

Q: 系统响应变慢怎么办？
A: 
- 检查数据库连接池配置
- 确认Redis缓存是否正常工作
- 查看系统日志中的警告信息
- 考虑增加服务器资源

Q: 如何优化大量API调用的场景？
A:
- 启用Redis缓存
- 调整连接池大小
- 使用负载均衡
- 实施请求队列

### 3. 安全相关

Q: 如何处理可疑的API调用？
A: 
- 系统会自动记录异常访问
- 检查系统日志中的警告
- 必要时手动禁用相关密钥
- 考虑配置IP白名单

## 维护指南

### 日常维护

1. 日志管理
```bash
# 轮转日志
logrotate /etc/logrotate.d/ai-proxy

# 检查日志大小
du -sh /var/log/ai-proxy/

# 清理旧日志
find /var/log/ai-proxy/ -name "*.log.*" -mtime +30 -delete
```

2. 数据库维护
```bash
# 备份数据库
pg_dump ai_proxy > backup_$(date +%Y%m%d).sql

# 优化数据库
VACUUM ANALYZE;

# 监控数据库大小
SELECT pg_size_pretty(pg_database_size('ai_proxy'));
```

3. 性能监控
```bash
# 检查系统资源
htop

# 监控API响应时间
tail -f /var/log/ai-proxy/access.log | grep response_time

# 检查Redis状态
redis-cli info | grep used_memory
```

### 故障处理

1. 服务无响应
```bash
# 检查服务状态
supervisorctl status ai-proxy

# 重启服务
supervisorctl restart ai-proxy

# 检查错误日志
tail -f /var/log/ai-proxy/err.log
```

2. 数据库连接问题
```bash
# 检查数据库状态
systemctl status postgresql

# 检查连接
psql -U aiproxy -d ai_proxy -c "SELECT 1"

# 重启数据库
systemctl restart postgresql
```

3. 缓存问题
```bash
# 清理Redis缓存
redis-cli FLUSHDB

# 重启Redis
systemctl restart redis
```

### 更新维护

1. 代码更新
```bash
# 备份当前版本
cp -r /path/to/your/app /path/to/your/app.bak

# 更新代码
git pull origin main

# 更新依赖
pip install -r requirements.txt

# 数据库迁移
flask db upgrade

# 重启服务
supervisorctl restart ai-proxy
```

2. 配置更新
```bash
# 备份配置
cp .env .env.bak

# 更新配置
vim .env

# 重新加载配置
supervisorctl restart ai-proxy
```

3. SSL证书更新
```bash
# 自动更新Let's Encrypt证书
certbot renew

# 重启Nginx
systemctl restart nginx
```

### 监控告警

1. 设置监控
   - CPU使用率超过80%
   - 内存使用率超过85%
   - 磁盘使用率超过90%
   - API响应时间超过2秒
   - 错误率超过1%

2. 告警通道
   - 邮件通知
   - Slack通知
   - 短信通知（紧急情况）

3. 监控指标
   - 系统资源使用情况
   - API调用量和成功率
   - 响应时间分布
   - 错误日志数量
   - 数据库性能指标

记得定期检查和更新这些维护程序，确保系统持续稳定运行。