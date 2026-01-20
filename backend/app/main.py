from fastapi import FastAPI
from starlette.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import Optional

from app.config import settings
from app.database import init_db, SessionLocal
from app.api.endpoints import albums, categories, scan, auth, static
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
app.include_router(static.router)

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
    
    注意: 不处理 /api/ 路径，这些路径由API路由处理
    """
    # 不处理API路径
    if path.startswith("api/"):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not found")
    
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



@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "app": settings.APP_NAME}
