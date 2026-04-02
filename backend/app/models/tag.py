"""
标签相关模型
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base


class Tag(Base):
    """标签表（基础分类单元）"""
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    type = Column(String, index=True)  # 'org', 'model', 'cosplayer', 'character', 'tag'
    description = Column(String)
    album_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Tag(name='{self.name}', type='{self.type}')>"


class Organization(Base):
    """套图表（有额外信息，关联标签）"""
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    tag_id = Column(Integer, ForeignKey('tags.id'), unique=True)
    album_count = Column(Integer, default=0)
    cover_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联
    tag = relationship("Tag", backref="organization")
    
    def __repr__(self):
        return f"<Organization(name='{self.name}')>"


class Model(Base):
    """模特表（有额外信息，关联标签）"""
    __tablename__ = "models"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    tag_id = Column(Integer, ForeignKey('tags.id'), unique=True)
    album_count = Column(Integer, default=0)
    cover_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联
    tag = relationship("Tag", backref="model")
    
    def __repr__(self):
        return f"<Model(name='{self.name}')>"
