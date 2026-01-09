# GirlAtlas 后端服务

基于 FastAPI 的图集管理后端服务，支持 CBZ 文件解析、标签分类和图片服务。

## 功能特性

- ✅ 5表数据模型（标签、套图、模特、图集、关联表）
- ✅ CBZ文件自动扫描和解析
- ✅ 智能标签分类（套图/模特/通用标签）
- ✅ RESTful API接口
- ✅ 图片懒加载和缓存
- ✅ 分页查询和多维度筛选
- ✅ 后台扫描任务

## 项目结构

```
backend/
├── app/
│   ├── api/
│   │   ├── endpoints/
│   │   │   ├── albums.py      # 图集API
│   │   │   ├── categories.py  # 分类API
│   │   │   └── scan.py        # 扫描API
│   │   └── deps.py            # 依赖注入
│   ├── services/
│   │   ├── scanner.py         # 文件扫描服务
│   │   └── archive.py         # CBZ处理服务
│   ├── models.py              # 数据模型
│   ├── schemas.py             # Pydantic模型
│   ├── database.py            # 数据库连接
│   ├── config.py              # 配置管理
│   └── main.py                # 应用入口
├── images/                    # CBZ文件目录
├── tmp/cache/                 # 图片缓存
├── requirements.txt           # 依赖列表
├── .env.example              # 环境变量示例
├── run.py                    # 启动脚本
└── girlatlas.db              # SQLite数据库
```

## 数据模型

### 5表结构

1. **Tag** - 标签表（基础分类单元）
2. **Organization** - 套图表（关联标签）
3. **Model** - 模特表（关联标签）
4. **Album** - 图集表（核心数据）
5. **AlbumTag** - 图集-标签关联表（多对多）

### 关系说明

```
Organization (1) ←→ (1) Tag
Model (1) ←→ (1) Tag
Album (N) ←→ (N) Tag (通过 AlbumTag)
```

## API接口

### 分类相关
- `GET /categories` - 获取分类树
- `GET /categories/org` - 获取套图列表
- `GET /categories/model` - 获取模特列表
- `GET /categories/tag` - 获取标签列表

### 图集相关
- `GET /albums` - 图集列表（支持分页、筛选、搜索）
- `GET /albums/{id}` - 图集详情
- `GET /albums/{id}/images` - 图集图片列表
- `GET /albums/{id}/images/{filename}` - 获取图片内容
- `POST /albums/{id}/refresh` - 刷新图集元数据

### 扫描相关
- `POST /scan` - 后台扫描
- `POST /scan/sync` - 同步扫描
- `POST /scan/cleanup?days=30` - 清理已删除的图集记录
- `POST /scan/cleanup/orphans` - 清理孤儿数据
- `GET /scan/stats/orphans` - 获取孤儿数据统计
- `GET /scan/stats` - 获取扫描统计信息

## 安装运行

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境

```bash
cp .env.example .env
# 编辑 .env 文件，根据需要修改配置
```

### 3. 准备数据

确保 `backend/images/` 目录存在，并放入 `.cbz` 文件：
```
backend/images/
├── xiuren/
│   ├── XiuRen秀人网__No.10000__阿汁__75P.cbz
│   └── XiuRen秀人网__No.10001__白茹雪__62P.cbz
```

### 4. 启动服务

```bash
# 开发模式（自动重载）
python run.py

# 或直接使用uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. 扫描文件

```bash
# 同步扫描
curl -X POST http://localhost:8000/scan/sync

# 或使用API文档
# 访问 http://localhost:8000/docs
```

## 使用示例

### 获取分类树
```bash
curl http://localhost:8000/categories
```

### 获取图集列表
```bash
# 所有图集
curl http://localhost:8000/albums

# 按套图筛选
curl http://localhost:8000/albums?org_id=1

# 按模特筛选
curl http://localhost:8000/albums?model_id=1

# 按标签筛选
curl http://localhost:8000/albums?tag_id=1

# 分页
curl http://localhost:8000/albums?page=1&size=20
```

### 获取图片
```bash
# 图片列表
curl http://localhost:8000/albums/1/images

# 单张图片
curl http://localhost:8000/albums/1/images/001.jpg

# 缩放图片
curl http://localhost:8000/albums/1/images/001.jpg?width=800&height=600
```

## 标签解析规则

文件名格式：`套图__序号__模特__页数.cbz`

示例：`XiuRen秀人网__No.10000__阿汁__75P.cbz`

解析结果：
- **套图**: 秀人网
- **模特**: 阿汁
- **标签**: 人像, 写真

## 缓存策略

1. **HTTP缓存**: ETag + Cache-Control
2. **内存缓存**: LRU缓存500张图片
3. **磁盘缓存**: 所有缓存统一7天过期
4. **定时清理**: 每天自动清理过期缓存

### 缓存类型
- **图片列表缓存**: 7天（内存 + 文件）
- **提取图片缓存**: 7天（内存 + 文件）
- **元数据缓存**: 7天（内存 + 文件）

## 开发说明

### 添加新功能
1. 在 `models.py` 添加数据模型
2. 在 `schemas.py` 添加响应模型
3. 在 `services/` 添加业务逻辑
4. 在 `api/endpoints/` 添加API接口

### 测试
```bash
# 初始化测试数据库
python -c "from app.database import init_db; init_db()"

# 扫描测试
curl -X POST http://localhost:8000/scan/sync

# 查看数据
sqlite3 girlatlas.db "SELECT * FROM albums;"
```

## 生产部署

### 使用 Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 使用 Gunicorn
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

## 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| DATABASE_URL | sqlite:///./girlatlas.db | 数据库连接 |
| APP_NAME | GirlAtlas API | 应用名称 |
| APP_VERSION | 0.1.0 | 版本号 |
| DEBUG | True | 调试模式 |
| IMAGES_DIR | ../images | 图片目录 |
| CACHE_DIR | ./tmp/cache | 缓存目录 |
| SCAN_INTERVAL | 3600 | 扫描间隔(秒) |

## 许可证

MIT