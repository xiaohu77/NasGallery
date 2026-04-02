"""
AI 相关模型
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base


class AlbumEmbedding(Base):
    """图集向量表（用于AI搜索）"""
    __tablename__ = "album_embeddings"
    
    id = Column(Integer, primary_key=True)
    album_id = Column(Integer, ForeignKey('albums.id'), unique=True, nullable=False)
    embedding = Column(LargeBinary, nullable=False)  # 512维 float32 向量 = 2048 bytes
    model_version = Column(String, default='clip-v1')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联
    album = relationship("Album", backref="embedding")
    
    def __repr__(self):
        return f"<AlbumEmbedding(album_id={self.album_id}, model='{self.model_version}')>"


class AIScanTask(Base):
    """AI扫描任务状态表"""
    __tablename__ = "ai_scan_tasks"
    
    id = Column(Integer, primary_key=True)
    task_id = Column(String, unique=True, nullable=False)  # UUID
    status = Column(String, default='pending')  # pending, running, completed, failed
    total_albums = Column(Integer, default=0)
    processed_albums = Column(Integer, default=0)
    failed_albums = Column(Integer, default=0)
    error_message = Column(String)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<AIScanTask(task_id='{self.task_id}', status='{self.status}')>"
