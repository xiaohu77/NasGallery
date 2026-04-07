"""
用户相关模型扩展 - 浏览历史和收藏
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from datetime import datetime

from .base import Base


class UserFavorite(Base):
    """用户收藏表"""
    __tablename__ = "user_favorites"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    album_id = Column(Integer, ForeignKey('albums.id'), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_user_favorites_user_album', 'user_id', 'album_id', unique=True),
    )


class UserHistory(Base):
    """用户浏览历史表"""
    __tablename__ = "user_history"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    album_id = Column(Integer, ForeignKey('albums.id'), nullable=False, index=True)
    viewed_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_user_history_user_viewed', 'user_id', 'viewed_at'),
    )