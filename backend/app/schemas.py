from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# 标签相关模型
class TagBase(BaseModel):
    name: str
    type: str
    description: Optional[str] = None

class TagResponse(TagBase):
    id: int
    album_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# 套图相关模型
class OrganizationBase(BaseModel):
    name: str
    description: Optional[str] = None

class OrganizationResponse(OrganizationBase):
    id: int
    album_count: int
    cover_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# 模特相关模型
class ModelBase(BaseModel):
    name: str
    description: Optional[str] = None

class ModelResponse(ModelBase):
    id: int
    album_count: int
    cover_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# 图集相关 models
class AlbumBase(BaseModel):
    title: str
    file_path: str
    file_name: str
    description: Optional[str] = None

class AlbumCreate(AlbumBase):
    image_count: Optional[int] = None
    cover_image: Optional[str] = None
    file_size: Optional[int] = None

class AlbumSummary(BaseModel):
    id: int
    title: str
    cover_url: str
    image_count: int
    tags: List[str] = []
    description: Optional[str] = None
    
    class Config:
        from_attributes = True

class AlbumResponse(AlbumBase):
    id: int
    image_count: Optional[int]
    cover_image: Optional[str]
    file_size: Optional[int]
    created_at: datetime
    updated_at: datetime
    tags: List[TagResponse] = []
    
    class Config:
        from_attributes = True

# 分类树模型
class CategoryTree(BaseModel):
    org: List[OrganizationResponse] = []
    model: List[ModelResponse] = []
    tag: List[TagResponse] = []

# 分页响应模型
class PagedResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[AlbumSummary]

# 扫描响应模型
class ScanResponse(BaseModel):
    success: bool
    message: str
    scanned_files: int
    new_albums: int
    updated_albums: int


# 用户相关模型
class UserBase(BaseModel):
    username: str
    email: str


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    created_at: datetime
    is_admin: int
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse