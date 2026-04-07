"""
图集相关模型
"""
from sqlalchemy import Column, Integer, String, DateTime, BigInteger, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base


class AlbumTag(Base):
    """图集-标签关联表（多对多）"""
    __tablename__ = "album_tags"
    
    album_id = Column(Integer, ForeignKey('albums.id'), primary_key=True)
    tag_id = Column(Integer, ForeignKey('tags.id'), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 添加索引
    __table_args__ = (
        Index('idx_album_tags_album_id', 'album_id'),
        Index('idx_album_tags_tag_id', 'tag_id'),
    )


class Album(Base):
    """图集表（核心表）"""
    __tablename__ = "albums"
    
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    file_path = Column(String, unique=True, nullable=False)
    file_name = Column(String, nullable=False)
    description = Column(String)
    
    # 元数据
    image_count = Column(Integer)
    cover_image = Column(String)
    cover_path = Column(String)
    file_size = Column(BigInteger)
    view_count = Column(Integer, default=0)  # 浏览次数
    album_type = Column(String, default='cbz')  # 'cbz' 或 'folder'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_scan_time = Column(DateTime)
    is_active = Column(Integer, default=1)  # 1=有效，0=已删除
    
    # 多对多标签关联
    tags = relationship("Tag", secondary="album_tags", backref="albums")
    
    # 添加索引
    __table_args__ = (
        Index('idx_albums_is_active', 'is_active'),
        Index('idx_albums_created_at', 'created_at'),
        Index('idx_albums_title', 'title'),
    )
    
    def __repr__(self):
        return f"<Album(title='{self.title}', image_count={self.image_count})>"
