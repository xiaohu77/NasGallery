"""
标签相关 Schema
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class TagBase(BaseModel):
    """标签基础模型"""
    name: str
    type: str
    description: Optional[str] = None


class TagResponse(TagBase):
    """标签响应模型"""
    id: int
    album_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class OrganizationBase(BaseModel):
    """套图基础模型"""
    name: str
    description: Optional[str] = None


class OrganizationResponse(OrganizationBase):
    """套图响应模型"""
    id: int
    album_count: int
    cover_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ModelBase(BaseModel):
    """模特基础模型"""
    name: str
    description: Optional[str] = None


class ModelResponse(ModelBase):
    """模特响应模型"""
    id: int
    album_count: int
    cover_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class CategoryTree(BaseModel):
    """分类树模型"""
    org: List[OrganizationResponse] = []
    model: List[ModelResponse] = []
    cosplayer: List[TagResponse] = []
    character: List[TagResponse] = []
    tag: List[TagResponse] = []
