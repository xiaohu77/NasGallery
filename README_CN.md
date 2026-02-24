# NasGallery

<p align="center">
  <a href="https://github.com/wwgxx/NasGallery">
    <img src="https://img.shields.io/github/stars/wwgxx/NasGallery?style=social" alt="GitHub stars">
    <img src="https://img.shields.io/github/forks/wwgxx/NasGallery?style=social" alt="GitHub forks">
    <img src="https://img.shields.io/github/license/wwgxx/NasGallery" alt="License">
  </a>
  <br>
  <a href="https://github.com/wwgxx/NasGallery/actions">
    <img src="https://img.shields.io/github/actions/workflow/status/wwgxx/NasGallery/ci.yml" alt="Build status">
  </a>
  <img src="https://img.shields.io/github/languages/top/wwgxx/NasGallery" alt="Language">
  <img src="https://img.shields.io/github/repo-size/wwgxx/NasGallery" alt="Repo size">
</p>

> 一个现代化的 Web 应用，用于管理和查看 CBZ 图片档案，提供精美的图集界面。

[English](./README.md) | 简体中文

## ⭐ 星星趋势

[![Star History Chart](https://api.star-history.com/svg?repos=wwgxx/NasGallery&type=Date)](https://star-history.com/#wwgxx/NasGallery&Timeline)

## ✨ 功能特性

- 📚 **CBZ 档案管理** - 完整支持 CBZ（Comic Book ZIP）图片压缩包
- 🖼️ **精美图集画廊** - 响应式瀑布流布局，支持灯箱查看
- 🔍 **智能搜索** - 支持按标题、组织、模特、标签搜索图集
- 🏷️ **分类体系** - 三级分类：组织 / 模特 / 标签
- ⚡ **高性能** - 多级缓存系统，支持缩略图生成
- 📱 **PWA 支持** - 可安装的 Web 应用，支持离线访问
- 🌙 **深色模式** - 内置主题切换支持
- 🔐 **安全认证** - 基于 JWT 的身份验证和角色管理
- 🚀 **自动扫描** - 自动扫描文件系统，发现新内容

## 🛠️ 技术栈

### 后端
| 技术 | 描述 |
|------|------|
| [FastAPI](https://fastapi.tiangolo.com/) | 现代 Python Web 框架 |
| [SQLAlchemy](https://www.sqlalchemy.org/) | SQL 工具和 ORM |
| [Pydantic](https://docs.pydantic.dev/) | 数据验证 |
| [Pillow](https://python-pillow.org/) | 图片处理 |

### 前端
| 技术 | 描述 |
|------|------|
| [React](https://react.dev/) | UI 库 |
| [TypeScript](https://www.typescriptlang.org/) | 类型安全 |
| [Vite](https://vitejs.dev/) | 构建工具 |
| [TailwindCSS](https://tailwindcss.com/) | 原子化 CSS 框架 |

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- npm 或 yarn

### 安装步骤

1. **克隆仓库**

```bash
git clone https://github.com/wwgxx/NasGallery.git
cd NasGallery
```

2. **后端配置**

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python -c "from app.database import init_db; init_db()"

# （可选）配置环境变量
cp ../.env.example .env
# 编辑 .env 文件
```

3. **前端配置**

```bash
cd frontend

# 安装依赖
npm install

# （可选）配置环境变量
cp .env.example .env
# 编辑 .env 文件
```

### 运行应用

**后端：**

```bash
cd backend
python run.py
# 或
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API 服务将在 `http://localhost:8000` 启动

**前端：**

```bash
cd frontend
npm run dev
```

应用将在 `http://localhost:5173` 启动

### 初始配置

1. 默认管理员账户：
   - 用户名：`admin`
   - 密码：`admin123`

2. 登录后进入扫描页面索引您的 CBZ 文件

3. 将 CBZ 文件放入 `data/images` 目录

## 📁 项目结构

```
NasGallery/
├── backend/
│   ├── app/
│   │   ├── api/endpoints/     # API 路由
│   │   ├── services/          # 业务逻辑
│   │   ├── models.py          # 数据库模型
│   │   ├── schemas.py         # Pydantic 模型
│   │   ├── database.py        # 数据库配置
│   │   └── main.py            # 应用入口
│   ├── data/                  # 数据目录
│   │   ├── images/            # CBZ 文件
│   │   └── tmp/               # 缓存文件
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/        # React 组件
│   │   ├── pages/            # 页面组件
│   │   ├── hooks/            # 自定义 Hooks
│   │   ├── contexts/         # React Context
│   │   ├── services/         # API 服务
│   │   └── types/            # TypeScript 类型
│   ├── public/
│   └── package.json
│
├── .env                       # 环境配置
├── docker-compose.yml         # Docker Compose
├── Dockerfile                 # Docker 镜像
└── README.md
```

## 📡 API 文档

服务启动后，访问以下地址查看 API 文档：

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🔧 配置说明

### 环境变量

| 变量 | 描述 | 默认值 |
|------|------|--------|
| `PROJECT_NAME` | 项目名称 | `GirlAtlas` |
| `DATABASE_URL` | 数据库 URL | `sqlite:///./data/nasgallery.db` |
| `SECRET_KEY` | JWT 密钥 | 自动生成 |
| `ADMIN_USERNAME` | 管理员用户名 | `admin` |
| `ADMIN_PASSWORD` | 管理员密码 | `admin123` |
| `IMAGES_DIR` | CBZ 文件目录 | `./data/images` |
| `VITE_API_BASE` | API 基础 URL | `http://localhost:8000` |

## 🐳 Docker 部署

```bash
# 使用 Docker Compose 构建和运行
docker-compose up -d

# 或单独构建
docker build -t nasgallery .
docker run -d -p 8000:8000 -v ./data:/app/data nasgallery
```

## 🤝 贡献指南

欢迎提交贡献！请随时提交 Pull Request。

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 打开 Pull Request

## 📄 开源许可证

本项目基于 MIT 许可证开源 - 请查看 [LICENSE](LICENSE) 文件了解详情。

---

<p align="center">
  由 <a href="https://github.com/wwgxx">wwgxx</a> ❤️ 开发
</p>
