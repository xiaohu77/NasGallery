"""
用户相关 Schema
"""
from pydantic import BaseModel
from datetime import datetime


class UserBase(BaseModel):
    """用户基础模型"""
    username: str
    email: str


class UserResponse(UserBase):
    """用户响应模型"""
    id: int
    created_at: datetime
    is_admin: int
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """用户登录模型"""
    username: str
    password: str


class Token(BaseModel):
    """令牌模型"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
