import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./girlatlas.db"
    
    # 应用配置
    APP_NAME: str = "GirlAtlas API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    
    # 路径配置
    BASE_DIR: Path = Path(__file__).parent.parent
    IMAGES_DIR: Path = BASE_DIR / "images"
    CACHE_DIR: Path = BASE_DIR / "tmp" / "cache"
    COVERS_DIR: Path = BASE_DIR / "tmp" / "covers"
    
    # 扫描配置
    SCAN_INTERVAL: int = 3600  # 秒
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()