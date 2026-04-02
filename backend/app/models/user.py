"""
用户相关模型
"""
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from .base import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Integer, default=1)  # 1=激活，0=禁用
    is_admin = Column(Integer, default=0)   # 1=管理员，0=普通用户
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<User(username='{self.username}', is_admin={self.is_admin})>"
