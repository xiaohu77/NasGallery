# GirlAtlas AGENTS.md

## 项目概述
GirlAtlas是一个双栈应用，包含FastAPI后端和React/TypeScript前端，用于管理和查看CBZ压缩包格式的图片档案。

## 构建/测试命令

### 后端 (Python/FastAPI)
```bash
# 安装依赖
cd backend
pip install -r requirements.txt

# 开发模式运行
python run.py
# 或
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 数据库初始化
python -c "from app.database import init_db; init_db()"

# 扫描测试
curl -X POST http://localhost:8000/scan/sync

# 运行测试 (如果使用pytest)
pytest tests/ -v
# 运行单个测试
pytest tests/test_file.py::test_function -v
```

**注意**: 管理员账户会在应用启动时自动初始化或更新。如果管理员账户不存在，会自动创建；如果已存在，会根据环境变量更新密码。

### 前端 (React/TypeScript/Vite)
```bash
cd frontend

# 安装依赖
npm install

# 开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览构建
npm run preview

# 类型检查
npx tsc --noEmit

# 运行测试 (如果配置)
npm test
# 运行单个测试
npm test -- --testNamePattern="测试名称"
```

## 代码风格指南

### 后端 (Python)

#### 导入顺序
```python
# 标准库
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime

# 第三方
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

# 本地 (绝对路径，从app开始)
from app.models import Album, Tag
from app.database import get_db
from app.config import settings
```

#### 命名规范
- **类**: PascalCase (`AlbumService`, `ScanLogger`)
- **函数/方法**: snake_case (`get_albums`, `extract_tags`)
- **变量**: snake_case (`album_count`, `cover_url`)
- **常量**: UPPER_SNAKE_CASE (`API_VERSION`, `CACHE_TTL`)
- **私有**: 前缀下划线 (`_internal_method`)

#### 类型提示
```python
from typing import List, Optional, Dict, Any

def get_albums(
    page: int = 1,
    size: int = 20,
    tag_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
) -> PagedResponse:
    ...
```

#### 错误处理
```python
from fastapi import HTTPException

# 使用具体状态码
raise HTTPException(status_code=404, detail="Album not found")

# 早期验证输入
if not file_path.exists():
    raise HTTPException(status_code=400, detail="Invalid file path")

# 外部操作使用try/except
try:
    result = await process_file(file_path)
except Exception as e:
    logger.error(f"Failed to process {file_path}: {e}")
    raise HTTPException(status_code=500, detail="Processing failed")
```

#### FastAPI模式
```python
router = APIRouter(prefix="/albums", tags=["albums"])

@router.get("/", response_model=PagedResponse)
async def get_albums(db: Session = Depends(get_db)):
    ...
```

### 前端 (React/TypeScript)

#### 导入顺序
```typescript
// React核心
import { useState, useEffect, useCallback, useRef } from 'react'
import type { ReactNode } from 'react'

// React Router
import { Link, useParams, useNavigate } from 'react-router-dom'

// 本地组件
import { useAlbums } from '../hooks/useAlbums'
import { AlbumSummary } from '../types/album'
import { ThemeProvider } from '../contexts/ThemeContext'

// 第三方服务
import { PWAService } from '../services/pwaService'
```

#### 命名规范
- **组件**: PascalCase (`Header`, `AlbumCard`, `ImageGrid`)
- **Hooks**: useCamelCase (`useAlbums`, `useTheme`, `useImageZoom`)
- **函数**: camelCase (`fetchAlbums`, `handleClick`)
- **接口/类型**: PascalCase (`AlbumSummary`, `ZoomState`)
- **变量**: camelCase (`albumCount`, `isLoading`)
- **常量**: UPPER_SNAKE_CASE (`API_BASE`, `CACHE_KEY`)

#### TypeScript模式
```typescript
// 明确类型
interface AlbumProps {
  id: number
  title: string
  coverImage?: string
}

// 避免'any' - 使用unknown或具体类型
const data: unknown = await response.json()

// 使用工具类型
type PartialAlbum = Partial<Album>
type RequiredAlbum = Required<Album>

// 可复用hooks的泛型
function useData<T>(fetcher: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null)
  ...
}
```

#### React模式
```typescript
const AlbumCard = ({ id, title }: AlbumProps): JSX.Element => {
  // 解构props
  // Hooks放在顶层
  const { theme } = useTheme()
  const navigate = useNavigate()
  
  // 记忆化昂贵计算
  const coverUrl = useMemo(() => {
    return `${API_BASE}/covers/${id}.jpg`
  }, [id])
  
  // 记忆化回调
  const handleClick = useCallback(() => {
    navigate(`/album/${id}`)
  }, [id, navigate])
  
  // useEffect处理副作用
  useEffect(() => {
    // 清理函数
    return () => {
      // 清理逻辑
    }
  }, [dependencies])
  
  return (
    <div onClick={handleClick}>
      {/* JSX */}
    </div>
  )
}
```

#### 错误处理
```typescript
// 异步操作使用try/catch
try {
  const response = await fetch(`${API_BASE}/albums`)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  const data = await response.json()
  return data
} catch (error) {
  console.error('Failed to fetch albums:', error)
  throw error // 重新抛出给调用者处理
}

// 类型守卫
function isAlbum(data: unknown): data is Album {
  return (
    typeof data === 'object' &&
    data !== null &&
    'id' in data &&
    'title' in data
  )
}
```

#### 状态管理
```typescript
// 使用函数式更新
const [count, setCount] = useState(0)
const increment = () => setCount(prev => prev + 1)

// 使用ref存储不触发重渲染的值
const hasRestoredFromCache = useRef(false)

// 使用callback处理传递给子组件的函数
const loadMore = useCallback(() => {
  // 逻辑
}, [dependencies])
```

### 数据库/模型

#### SQLAlchemy模型
```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

class Album(Base):
    __tablename__ = "albums"
    
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    file_path = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    tags = relationship("Tag", secondary="album_tags", backref="albums")
```

#### Pydantic模式
```python
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class AlbumBase(BaseModel):
    title: str
    description: Optional[str] = None

class AlbumResponse(AlbumBase):
    id: int
    file_path: str
    created_at: datetime
    tags: List[TagResponse]
    
    class Config:
        from_attributes = True
```

## 文件结构约定

### 后端
```
backend/
├── app/
│   ├── api/
│   │   └── endpoints/
│   │       ├── albums.py
│   │       ├── categories.py
│   │       └── scan.py
│   ├── services/
│   │   ├── scanner.py
│   │   ├── archive.py
│   │   ├── cover.py
│   │   └── cache.py
│   ├── models.py
│   ├── schemas.py
│   ├── database.py
│   ├── config.py
│   └── main.py
├── data/images/          # CBZ文件目录
├── data/tmp/             # 缓存和封面
└── data/girlatlas.db    # SQLite数据库
```

### 前端
```
frontend/
├── src/
│   ├── components/
│   │   ├── Album/
│   │   ├── Lightbox/
│   │   ├── icons/
│   │   └── Header.tsx
│   ├── contexts/
│   │   ├── ThemeContext.tsx
│   │   └── OfflineContext.tsx
│   ├── hooks/
│   │   ├── useAlbums.ts
│   │   ├── useImageZoom.ts
│   │   └── useLightbox.ts
│   ├── pages/
│   │   ├── Home.tsx
│   │   └── AlbumDetail.tsx
│   ├── services/
│   │   └── pwaService.ts
│   ├── types/
│   │   └── album.ts
│   ├── utils/
│   │   └── cache.ts
│   ├── App.tsx
│   └── main.tsx
├── public/
└── index.html
```

## 环境变量

### 后端 (.env)
```bash
DATABASE_URL=sqlite:///./data/girlatlas.db
APP_NAME=GirlAtlas API
APP_VERSION=0.1.0
DEBUG=True
IMAGES_DIR=./data/images
CACHE_DIR=./data/tmp/cache
```

### 前端 (.env)
```bash
VITE_API_BASE=http://localhost:8000
```

## 常见模式

### 数据获取
```typescript
const fetchAlbums = async (page: number, categoryId?: number) => {
  const params = new URLSearchParams({
    page: page.toString(),
    ...(categoryId && { tag_id: categoryId.toString() })
  })
  
  const response = await fetch(`${API_BASE}/albums?${params}`)
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  return response.json()
}
```

### 组件组合
```typescript
// 容器组件
const AlbumListContainer = () => {
  const { albums, loading } = useAlbums()
  if (loading) return <Skeleton />
  return <AlbumList albums={albums} />
}

// 展示组件
const AlbumList = ({ albums }: { albums: Album[] }) => (
  <div className="grid">
    {albums.map(album => (
      <AlbumCard key={album.id} {...album} />
    ))}
  </div>
)
```

## Git工作流

### 提交信息
```
feat: 添加图片缩放功能
fix: 修复灯箱内存泄漏
refactor: 简化专辑数据获取
docs: 更新API端点文档
style: 统一代码格式
```

### 分支命名
```
feature/lightbox-zoom
fix/scroll-position-restoration
refactor/api-response-types
```

## 调试技巧

### 后端
```bash
# 查看日志
tail -f app.log

# 调试SQL查询
echo "SELECT * FROM albums;" | sqlite3 data/girlatlas.db

# 测试API
curl -v http://localhost:8000/health
```

### 前端
```typescript
// 添加调试日志
console.log('State:', state)

// React DevTools检查组件重渲染和props

// 浏览器网络标签页监控API调用和响应时间
```

## 安全最佳实践

1. **输入验证**: 始终验证和清理用户输入
2. **SQL注入**: 使用ORM参数化查询
3. **XSS防护**: 在React中转义用户内容
4. **CORS**: 正确配置允许的源
5. **文件上传**: 验证文件类型和大小
6. **环境变量**: 永远不要提交密钥
7. **HTTPS**: 生产环境使用HTTPS

这个AGENTS.md应该随着项目发展而更新。保持与采用的新模式、工具或约定同步。