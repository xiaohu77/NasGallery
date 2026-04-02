"""
图集相关 Schema
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from .tag import TagResponse


class AlbumBase(BaseModel):
    """图集基础模型"""
    title: str
    file_path: str
    file_name: str
    description: Optional[str] = None


class AlbumCreate(AlbumBase):
    """图集创建模型"""
    image_count: Optional[int] = None
    cover_image: Optional[str] = None
    file_size: Optional[int] = None


class AlbumSummary(BaseModel):
    """图集摘要模型（用于列表展示）"""
    id: int
    title: str
    cover_url: Optional[str] = None
    image_count: int
    tags: List[str] = []
    description: Optional[str] = None
    
    class Config:
        from_attributes = True


class AlbumResponse(AlbumBase):
    """图集响应模型（完整信息）"""
    id: int
    image_count: Optional[int]
    cover_image: Optional[str]
    file_size: Optional[int]
    created_at: datetime
    updated_at: datetime
    tags: List[TagResponse] = []
    
    class Config:
        from_attributes = True


class ScanResponse(BaseModel):
    """扫描响应模型"""
    success: bool
    message: str
    scanned_files: int
    new_albums: int
    updated_albums: int
    task_id: Optional[str] = None
