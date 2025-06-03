# API密钥管理系统

## 项目简介

API密钥管理系统是一个专门设计用于管理和监控API密钥的Web应用程序。它提供了完整的API密钥生命周期管理、使用统计分析和系统监控功能。

## 主要功能

### 1. API密钥管理
- 创建和管理API密钥
- 设置密钥有效期和使用限制
- 实时监控密钥使用情况
- 一键启用/禁用密钥

### 2. 使用统计
- 实时调用统计
- 提供商使用分布
- 响应时间分析
- 成功率统计

### 3. 系统监控
- 详细的系统日志
- 性能监控
- 异常告警
- 安全审计

## 技术栈

- 后端：Python + Flask
- 数据库：PostgreSQL
- 缓存：Redis
- 前端：Bootstrap + Chart.js
- 部署：Nginx + Gunicorn

## 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件：

```ini
DATABASE_URL=postgresql://user:password@localhost/dbname
SECRET_KEY=your-secret-key
FLASK_ENV=development
```

### 3. 初始化数据库

```bash
flask db upgrade
flask create-admin
```

### 4. 运行开发服务器

```bash
flask run
```

访问 `http://localhost:5000/admin` 进入管理界面。

## 项目文档

- [部署指南](docs/deployment_guide.md) - 详细的部署和维护说明
- [快速入门](docs/quickstart.md) - 新用户指南
- [API文档](docs/api_docs.md) - API接口说明

## 系统要求

- Python 3.8+
- PostgreSQL 12+
- Redis 6.0+（可选，用于缓存）
- 现代浏览器（支持ES6+）

## 开发设置

1. 克隆仓库
```bash
git clone https://github.com/yourusername/api-key-manager.git
cd api-key-manager
```

2. 安装开发依赖
```bash
pip install -r requirements-dev.txt
```

3. 设置pre-commit钩子
```bash
pre-commit install
```

4. 运行测试
```bash
pytest
```

## 项目结构

```
api-key-manager/
├── app/
│   ├── __init__.py
│   ├── models/
│   ├── routes/
│   ├── services/
│   └── utils/
├── docs/
│   ├── deployment_guide.md
│   ├── quickstart.md
│   └── api_docs.md
├── templates/
│   └── admin/
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

## 特性亮点

1. 安全性
   - 密钥自动轮换
   - 访问控制
   - 审计日志
   - 异常检测

2. 可扩展性
   - 模块化设计
   - 插件系统
   - API支持
   - 自定义集成

3. 易用性
   - 直观的界面
   - 详细的统计
   - 灵活的配置
   - 完整的文档

## 最佳实践

1. 密钥管理
   - 定期更换密钥
   - 设置使用限制
   - 监控异常使用
   - 及时清理过期密钥

2. 系统维护
   - 定期备份数据
   - 监控系统资源
   - 检查错误日志
   - 更新安全补丁

3. 性能优化
   - 使用缓存
   - 优化数据库
   - 控制并发
   - 监控响应时间

## 常见问题

1. Q: 如何重置管理员密码？
   A: 使用命令 `flask reset-admin-password`

2. Q: 如何备份数据？
   A: 参考[部署指南](docs/deployment_guide.md)中的备份说明

3. Q: 如何处理性能问题？
   A: 检查系统日志，优化数据库，考虑使用缓存

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 版本历史

- v1.0.0 (2024-01-20)
  - 初始版本发布
  - 基本的密钥管理功能
  - 使用统计和监控

- v1.1.0 (计划中)
  - 批量操作功能
  - 更多统计图表
  - 性能优化
  - API增强

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 联系方式

- 项目维护者：[维护者姓名]
- 邮箱：[联系邮箱]
- 问题反馈：[Issue 页面]

## 致谢

感谢所有贡献者的付出！

## 状态徽章

![Build Status](https://img.shields.io/travis/yourusername/api-key-manager)
![Coverage](https://img.shields.io/codecov/c/github/yourusername/api-key-manager)
![License](https://img.shields.io/github/license/yourusername/api-key-manager)