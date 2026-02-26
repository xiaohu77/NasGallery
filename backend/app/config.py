import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./data/nasgallery.db"
    
    # 应用配置
    APP_NAME: str = "NasGallery API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    
    # 路径配置
    BASE_DIR: Path = Path(__file__).parent.parent
    IMAGES_DIR: Path = BASE_DIR / "data" / "images"
    CACHE_DIR: Path = BASE_DIR / "data" / "tmp" / "cache"
    COVERS_DIR: Path = BASE_DIR / "data" / "tmp" / "covers"
    THUMBNAIL_DIR: Path = BASE_DIR / "data" / "tmp" / "thumbnail"
    
    # 图片子目录配置
    COMIC_DIR: Path = IMAGES_DIR / "comic"
    COSPLAY_CHARACTER_DIR: Path = IMAGES_DIR / "cosplay" / "character"
    COSPLAY_ORG_DIR: Path = IMAGES_DIR / "cosplay" / "org"
    PHOTOBOOK_CHARACTER_DIR: Path = IMAGES_DIR / "photobook" / "character"
    PHOTOBOOK_ORG_DIR: Path = IMAGES_DIR / "photobook" / "org"
    
    # 扫描配置
    SCAN_INTERVAL: int = 3600  # 秒
    
    # 标签关键字配置
    TAG_KEYWORDS: str = "风景,人像,动漫,CG,厚涂,油画,漫画,水彩,国画"
    
    # JWT配置
    SECRET_KEY: str = "nasgallery-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天
    
    # 管理员配置
    ADMIN_USERNAME: str = "admin"
    ADMIN_EMAIL: str = "admin@nasgallery.com"
    ADMIN_PASSWORD: str = "admin123"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()