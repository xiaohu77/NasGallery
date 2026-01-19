from fastapi import FastAPI
from starlette.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import Optional

from app.config import settings
from app.database import init_db, SessionLocal
from app.api.endpoints import albums, categories, scan, auth
from app.models import User
from passlib.context import CryptContext

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
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
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

# 挂载静态文件目录（前端构建产物）
try:
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
        # 也挂载assets目录（Vite构建产物）
        assets_dir = static_dir / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
except Exception as e:
    print(f"Warning: Failed to mount static files: {e}")

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    # 确保必要的目录存在
    settings.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    settings.IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    settings.COVERS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 初始化数据库
    init_db()
    
    # 初始化或更新管理员账户
    await _init_or_update_admin_user()
    
    # 初始化缓存服务（触发定时清理任务）
    from app.services.cache import cache_service
    print(f"应用启动: {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"数据库: {settings.DATABASE_URL}")
    print(f"图片目录: {settings.IMAGES_DIR}")
    print(f"封面目录: {settings.COVERS_DIR}")
    print(f"缓存目录: {settings.CACHE_DIR}")
    print(f"缓存服务已启动，定时清理任务运行中...")


async def _init_or_update_admin_user():
    """初始化或更新管理员账户"""
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    db = SessionLocal()
    try:
        # 检查管理员是否已存在
        existing_admin = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
        
        if existing_admin:
            # 更新管理员密码
            existing_admin.hashed_password = pwd_context.hash(settings.ADMIN_PASSWORD)
            existing_admin.email = settings.ADMIN_EMAIL
            db.commit()
            print(f"管理员账户 '{settings.ADMIN_USERNAME}' 密码已更新")
        else:
            # 创建管理员账户
            admin_user = User(
                username=settings.ADMIN_USERNAME,
                email=settings.ADMIN_EMAIL,
                hashed_password=pwd_context.hash(settings.ADMIN_PASSWORD),
                is_active=1,
                is_admin=1,
            )
            db.add(admin_user)
            db.commit()
            print(f"管理员账户 '{settings.ADMIN_USERNAME}' 初始化成功")
            print(f"用户名: {admin_user.username}")
            print(f"邮箱: {admin_user.email}")
            print(f"用户ID: {admin_user.id}")
            print(f"管理员权限: {'是' if admin_user.is_admin else '否'}")
    except Exception as e:
        print(f"初始化或更新管理员账户失败: {e}")
        db.rollback()
    finally:
        db.close()

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理"""
    print("应用关闭")

@app.get("/", response_class=FileResponse)
async def root():
    """根路径 - 提供前端页面"""
    static_dir = Path(__file__).parent / "static"
    index_path = static_dir / "index.html"
    
    if index_path.exists():
        return FileResponse(index_path)
    else:
        # 如果静态文件不存在，返回API信息
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "running",
            "docs": "/docs",
            "redoc": "/redoc"
        }

@app.get("/{path:path}", response_class=FileResponse)
async def catch_all(path: str):
    """
    通配符路由 - 处理所有未匹配的路径
    这允许前端的 React Router 处理页面路由
    """
    static_dir = Path(__file__).parent / "static"
    index_path = static_dir / "index.html"
    
    # 检查请求的路径是否是静态文件
    requested_path = static_dir / path
    
    # 如果请求的是静态文件且存在，直接返回
    if requested_path.exists() and requested_path.is_file():
        return FileResponse(requested_path)
    
    # 否则返回前端的 index.html，让 React Router 处理路由
    if index_path.exists():
        return FileResponse(index_path)
    
    # 如果静态文件不存在，返回API信息
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/sw.js", response_class=FileResponse)
async def service_worker():
    """提供Service Worker文件"""
    static_dir = Path(__file__).parent / "static"
    sw_path = static_dir / "sw.js"
    
    if not sw_path.exists():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Service Worker not found")
    
    return FileResponse(
        sw_path,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.get("/manifest.json", response_class=FileResponse)
async def manifest():
    """提供PWA清单文件"""
    static_dir = Path(__file__).parent / "static"
    manifest_path = static_dir / "manifest.json"
    
    if not manifest_path.exists():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Manifest not found")
    
    return FileResponse(
        manifest_path,
        headers={
            "Cache-Control": "public, max-age=3600"
        }
    )

@app.get("/icon-192.png", response_class=FileResponse)
async def icon_192():
    """提供192x192图标"""
    static_dir = Path(__file__).parent / "static"
    icon_path = static_dir / "icon-192.png"
    
    if not icon_path.exists():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Icon not found")
    
    return FileResponse(
        icon_path,
        headers={
            "Cache-Control": "public, max-age=86400"
        }
    )

@app.get("/icon-512.png", response_class=FileResponse)
async def icon_512():
    """提供512x512图标"""
    static_dir = Path(__file__).parent / "static"
    icon_path = static_dir / "icon-512.png"
    
    if not icon_path.exists():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Icon not found")
    
    return FileResponse(
        icon_path,
        headers={
            "Cache-Control": "public, max-age=86400"
        }
    )

@app.get("/icon.svg", response_class=FileResponse)
async def icon_svg():
    """提供SVG图标"""
    static_dir = Path(__file__).parent / "static"
    icon_path = static_dir / "icon.svg"
    
    if not icon_path.exists():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Icon not found")
    
    return FileResponse(
        icon_path,
        headers={
            "Cache-Control": "public, max-age=86400"
        }
    )

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