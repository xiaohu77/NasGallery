from fastapi import FastAPI
from starlette.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pathlib import Path
from typing import Optional

from app.config import settings
from app.database import init_db
from app.api.endpoints import albums, categories, scan, auth

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="GirlAtlas 后端API服务",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://dev.xiaohu777.cn",
        "https://dev.xiaohu777.cn",
        "https://back.xiaohu777.cn",
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip压缩
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 注册路由
app.include_router(albums.router)
app.include_router(categories.router)
app.include_router(scan.router)
app.include_router(auth.router)

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    # 确保必要的目录存在
    settings.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    settings.IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    settings.COVERS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 初始化数据库
    init_db()
    
    # 初始化缓存服务（触发定时清理任务）
    from app.services.cache import cache_service
    print(f"应用启动: {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"数据库: {settings.DATABASE_URL}")
    print(f"图片目录: {settings.IMAGES_DIR}")
    print(f"封面目录: {settings.COVERS_DIR}")
    print(f"缓存目录: {settings.CACHE_DIR}")
    print(f"缓存服务已启动，定时清理任务运行中...")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理"""
    print("应用关闭")

@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "app": settings.APP_NAME}

@app.get("/covers/{cover_name}")
async def serve_cover(cover_name: str):
    """
    提供预提取的封面图（静态文件服务）
    cover_name: CBZ文件名.jpg，例如 XiuRen__No.10000__阿汁__75P.jpg
    """
    cover_path = settings.COVERS_DIR / cover_name
    
    if not cover_path.exists():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="封面不存在")
    
    return FileResponse(
        cover_path,
        headers={
            "Cache-Control": "public, max-age=86400",  # 24小时缓存
            "ETag": f'"{cover_path.stat().st_mtime}"'
        }
    )

@app.get("/covers/stats")
async def cover_stats():
    """获取封面统计信息"""
    from app.services.cover import CoverService
    cover_service = CoverService(settings.COVERS_DIR)
    return cover_service.get_stats()