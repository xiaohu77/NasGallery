# NasGallery

<p align="center">
  <a href="https://github.com/xiaohu77/NasGallery">
    <img src="https://img.shields.io/github/stars/xiaohu77/NasGallery?style=social" alt="GitHub stars">
    <img src="https://img.shields.io/github/forks/xiaohu77/NasGallery?style=social" alt="GitHub forks">
    <img src="https://img.shields.io/github/license/xiaohu77/NasGallery" alt="License">
  </a>
  <br>
  <a href="https://github.com/xiaohu77/NasGallery/actions">
    <img src="https://img.shields.io/github/actions/workflow/status/xiaohu77/NasGallery/ci.yml" alt="Build status">
  </a>
  <img src="https://img.shields.io/github/languages/top/xiaohu77/NasGallery" alt="Language">
  <img src="https://img.shields.io/github/repo-size/xiaohu77/NasGallery" alt="Repo size">
</p>

> 一个现代化的 Web 应用，用于管理和查看 CBZ 图片档案，提供精美的图集界面。

简体中文 | [English](./README_EN.md)

## ✨ 功能特性

- 📚 **CBZ 档案管理** - 完整支持 CBZ（Comic Book ZIP）图片压缩包
- 🖼️ **精美图集画廊** - 响应式瀑布流布局，支持灯箱查看
- 🔍 **智能搜索** - 支持按标题、组织、模特、标签搜索图集
- 🤖 **AI 以文搜图** - 基于 CLIP 模型的语义搜索，用自然语言描述查找图集
- 🏷️ **分类体系** - 一级分类：所有图集 / 刊物 / 人物 / Cosplayer / 角色
- ⚡ **高性能** - 多级缓存系统，支持缩略图生成，优化大数据量查询
- 📱 **PWA 支持** - 可安装的 Web 应用，支持离线访问
- 🌙 **深色模式** - 内置主题切换支持
- 🔐 **安全认证** - 基于 JWT 的身份验证和角色管理
- 🚀 **自动扫描** - 异步扫描任务，支持断点续传
- 🎮 **GPU 加速** - 支持 Intel GPU (OpenVINO) 和 NVIDIA GPU (CUDA) 加速 AI 推理
- 📊 **扫描进度** - 实时显示扫描进度，支持暂停/恢复

## 🛠️ 技术栈

### 后端
| 技术 | 描述 |
|------|------|
| [FastAPI](https://fastapi.tiangolo.com/) | 现代 Python Web 框架 |
| [SQLAlchemy](https://www.sqlalchemy.org/) | SQL 工具和 ORM |
| [Pydantic](https://docs.pydantic.dev/) | 数据验证 |
| [Pillow](https://python-pillow.org/) | 图片处理 |
| [ONNX Runtime](https://onnxruntime.ai/) | AI 模型推理引擎 |
| [Chinese-CLIP](https://github.com/OFA-Sys/Chinese-CLIP) | 中文图文对齐模型 |

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

2. 登录后进入设置页面扫描您的 CBZ 文件

3. 将 CBZ 文件放入 `data/images` 目录

### AI 搜索配置（可选）

AI 搜索功能需要额外配置：

1. **下载 Chinese-CLIP 模型**

```bash
# 创建模型目录
mkdir -p backend/data/ai_models/chinese-clip

# 下载基础版模型（约 754MB）
cd backend/data/ai_models/chinese-clip
wget https://huggingface.co/Xenova/chinese-clip-vit-base-patch16/resolve/main/onnx/model.onnx -O model.onnx

# 下载 tokenizer
mkdir -p tokenizer
wget https://huggingface.co/bert-base-chinese/resolve/main/vocab.txt -O tokenizer/vocab.txt
```

2. **安装 GPU 加速支持（可选）**

```bash
# Intel GPU (OpenVINO) - 推荐集成显卡
pip install onnxruntime-openvino

# NVIDIA GPU (CUDA) - 需要 NVIDIA 显卡
pip install onnxruntime-gpu
```

3. **初始化 AI 向量**

进入设置页面 → AI 搜索 → 点击"扫描"按钮

4. **使用 AI 搜索**

在搜索框点击 💡 图标切换到 AI 搜索模式，输入自然语言描述即可搜索

## 📋 图集元数据要求

### 元数据文件

每个 CBZ 压缩包内可包含 `metadata.json` 文件来定义图集元数据。

### metadata.json 格式

```json
{
  "institution": "机构名称",
  "model": "模特名称",
  "cosplayer": "Cosplayer 名称",
  "character": "角色名称",
  "title": "图集标题",
  "description": "图集描述"
}
```

### 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| `institution` | 否 | 套图组织/机构名称 |
| `model` | 否 | 模特名称 |
| `cosplayer` | 否 | Cosplayer 名称 |
| `character` | 否 | 角色名称 |
| `title` | 是 | 图集标题 |
| `description` | 否 | 图集描述 |

### 文件命名规范

如果 CBZ 文件内没有 `metadata.json`，系统会尝试从文件名解析元数据。

**命名格式：**

```
机构名__其他信息__模特名称__页数P.jpg
```

**示例：**

```
优衣库__2024.01.15__张三__75P.cbz
```

解析结果：
- 组织：`优衣库`
- 模特：`张三`

### 目录结构

```
data/images/
├── org/                    # 按机构分类
│   ├── 优衣库/
│   │   ├── 优衣库__张三__75P.cbz
│   │   └── 优衣库__李四__80P.cbz
│   └── ...
├── model/                  # 按模特分类
│   ├── 张三/
│   │   └── 张三__写真集__100P.cbz
│   └── ...
├── cosplayer/              # 按 Cosplayer 分类
│   ├── cosplayer_name/
│   │   └── cosplay_album.cbz
│   └── ...
├── character/              # 按角色分类
│   ├── character_name/
│   │   └── character_album.cbz
│   └── ...
└── 机构名__模特名__100P/    # 文件夹图集
    ├── metadata.json
    ├── 001.jpg
    ├── 002.jpg
    └── ...
```

### 自动分类

系统会根据元数据和目录结构自动提取以下标签：

- **刊物 (org)**: 从 `institution` 字段或 `org/` 目录提取
- **人物 (model)**: 从 `model` 字段或 `model/` 目录提取
- **Cosplayer (cosplayer)**: 从 `cosplayer` 字段或 `cosplayer/` 目录提取
- **角色 (character)**: 从 `character` 字段或 `character/` 目录提取
- **标签 (tags)**: 从 `title` 和 `description` 中匹配关键词

支持的标签关键词：风景,人像,动漫,CG,厚涂,油画,漫画,水彩,国画

## 🔧 配置说明

### 环境变量

| 变量 | 描述 | 默认值 |
|------|------|--------|
| `PROJECT_NAME` | 项目名称 | `NasGallery` |
| `DATABASE_URL` | 数据库 URL | `sqlite:///./data/nasgallery.db` |
| `SECRET_KEY` | JWT 密钥 | 自动生成 |
| `ADMIN_USERNAME` | 管理员用户名 | `admin` |
| `ADMIN_PASSWORD` | 管理员密码 | `admin123` |
| `IMAGES_DIR` | CBZ 文件目录 | `./data/images` |
| `VITE_API_BASE` | API 基础 URL | `http://localhost:8000` |
| `TAG_KEYWORDS` | 标签关键字（逗号分隔） | 风景,人像,动漫,CG,厚涂,油画,漫画,水彩,国画 |

## 🐳 Docker 部署

```bash
# 使用 Docker Compose 构建和运行
docker-compose up -d

# 或单独构建
docker build -t nasgallery .
docker run -d -p 8000:8000 -v ./data:/app/data nasgallery
```

## 项目demo

https://nasgallery.xiaohu777.cn/

## 📄 开源许可证

本项目基于 MIT 许可证开源 - 请查看 [LICENSE](LICENSE) 文件了解详情。

---

<p align="center">
  由 <a href="https://github.com/xiaohu77">xiaohu77</a> ❤️ 开发
</p>

## ⭐ 星星趋势

[![Star History Chart](https://api.star-history.com/svg?repos=xiaohu77/NasGallery&type=Date)](https://star-history.com/#xiaohu77/NasGallery&Timeline)
