# 组会文献查重管理系统

一个专为课题组设计的文献管理与查重系统，支持局域网多人共享使用。

## 功能特点

- **文献管理**：上传、编辑、删除PDF文献，支持批量操作
- **智能查重**：自动检测重复文献，显示相似度和来源
- **权限管理**：管理员和普通成员两种角色，精细化权限控制
- **多人共享**：局域网内多人同时访问，数据实时同步
- **检索导出**：多条件搜索筛选，支持导出Excel
- **操作日志**：完整记录所有操作，便于追溯

## 技术栈

- 后端：Python Django 4.2
- 数据库：SQLite（默认）/ MySQL
- 前端：Bootstrap 5 + jQuery
- 查重：TF-IDF + 余弦相似度 / 外部API

## 快速开始

### 1. 环境要求

- Python 3.10+
- pip 包管理器

### 2. 安装步骤

```bash
# 进入项目目录
cd literature_system

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 复制环境变量配置
cp .env.example .env

# 创建日志目录
mkdir logs

# 初始化数据库
python manage.py migrate

# 初始化系统（创建管理员账号）
python manage.py init_system

# 启动开发服务器
python manage.py runserver 0.0.0.0:8000
```

### 3. 访问系统

打开浏览器访问：`http://localhost:8000`

默认管理员账号：
- 用户名：`admin`
- 密码：`admin123`

**⚠️ 首次登录后请立即修改管理员密码！**

## 局域网部署

### Windows 部署

```bash
# 1. 安装依赖（同上）

# 2. 使用 Waitress 生产服务器
pip install waitress

# 3. 启动服务（绑定所有网卡）
waitress-serve --port=8000 --host=0.0.0.0 config.wsgi:application
```

局域网内其他电脑通过 `http://服务器IP:8000` 访问。

### Linux 部署（推荐）

```bash
# 1. 安装依赖
pip install -r requirements.txt
pip install gunicorn

# 2. 收集静态文件
python manage.py collectstatic

# 3. 使用 Gunicorn 启动
gunicorn --bind 0.0.0.0:8000 --workers 4 config.wsgi:application
```

### Nginx 反向代理（可选）

```nginx
server {
    listen 80;
    server_name 192.168.1.100;  # 服务器IP

    location /static/ {
        alias /path/to/literature_system/staticfiles/;
    }

    location /media/ {
        alias /path/to/literature_system/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 使用 MySQL 数据库

当用户数较多时，建议使用 MySQL：

```bash
# 1. 安装 MySQL
# 2. 创建数据库
CREATE DATABASE literature_db CHARACTER SET utf8mb4;

# 3. 修改 .env 文件
DB_NAME=literature_db
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306

# 4. 修改 config/settings.py，取消 MySQL 配置的注释

# 5. 重新迁移数据库
python manage.py migrate
```

## 功能说明

### 用户角色

| 角色 | 权限 |
|------|------|
| 管理员 | 全部权限：增删改所有文献、管理用户、查看日志、系统设置 |
| 普通成员 | 上传文献、查重、查看列表、下载文献、修改/删除自己的文献 |

### 查重功能

系统提供两种查重方式：

1. **本地查重**（默认）
   - 提取PDF文本内容
   - 使用TF-IDF计算相似度
   - 与库中已有文献比对

2. **外部API查重**（需配置）
   - 配置 `.env` 中的 `PLAGIARISM_API_URL` 和 `PLAGIARISM_API_KEY`
   - 支持接入第三方查重服务

### 文献字段

- 基本信息：标题、作者、期刊、年份、DOI、关键词、摘要
- 组会信息：分享人、组会日期、备注
- 系统信息：上传者、上传时间、文件大小

## 目录结构

```
literature_system/
├── config/                 # Django配置
│   ├── settings.py        # 主配置文件
│   ├── urls.py            # URL路由
│   └── wsgi.py            # WSGI入口
├── literature/            # 主应用
│   ├── models.py          # 数据模型
│   ├── views.py           # 视图函数
│   ├── forms.py           # 表单定义
│   ├── services.py        # 业务服务（查重等）
│   ├── middleware.py      # 中间件
│   └── management/        # 管理命令
├── templates/             # 模板文件
│   └── literature/        # 页面模板
├── static/                # 静态文件
├── media/                 # 上传文件存储
│   └── literature/        # PDF文件
├── logs/                  # 日志文件
├── manage.py              # Django管理脚本
├── requirements.txt       # 依赖列表
└── .env                   # 环境变量
```

## 安全说明

- ✅ 密码使用 bcrypt 加密存储
- ✅ CSRF 防护
- ✅ XSS 防护
- ✅ SQL 注入防护
- ✅ 文件类型验证（仅PDF）
- ✅ 文件大小限制（默认50MB）
- ✅ 操作日志记录
- ✅ 权限验证

## 常见问题

### Q: 无法访问系统？

1. 检查防火墙是否开放端口
2. 确认服务绑定的是 `0.0.0.0` 而不是 `127.0.0.1`
3. 检查服务器IP是否正确

### Q: 上传文件失败？

1. 检查 `media/` 目录权限
2. 确认文件是PDF格式
3. 检查文件大小是否超过限制

### Q: 查重结果不准确？

1. 调整相似度阈值（系统设置）
2. PDF可能是扫描版，无法提取文本
3. 考虑接入专业查重API

## 开发者

如需二次开发，请参考：

- Django文档：https://docs.djangoproject.com/
- 模型定义：`literature/models.py`
- 视图逻辑：`literature/views.py`
- 查重服务：`literature/services.py`

## 许可证

MIT License