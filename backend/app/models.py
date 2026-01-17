from sqlalchemy import Column, Integer, String, DateTime, BigInteger, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

# 图集-标签关联表（多对多）
class AlbumTag(Base):
    __tablename__ = "album_tags"
    
    album_id = Column(Integer, ForeignKey('albums.id'), primary_key=True)
    tag_id = Column(Integer, ForeignKey('tags.id'), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# 标签表（基础分类单元）
class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    type = Column(String, index=True)  # 'org', 'model', 'tag'
    description = Column(String)
    album_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Tag(name='{self.name}', type='{self.type}')>"

# 套图表（有额外信息，关联标签）
class Organization(Base):
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

# 模特表（有额外信息，关联标签）
class Model(Base):
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

# 图集表（核心表）
class Album(Base):
    __tablename__ = "albums"
    
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    file_path = Column(String, unique=True, nullable=False)
    file_name = Column(String, nullable=False)
    description = Column(String)  # 新增描述字段
    
    # 元数据
    image_count = Column(Integer)
    cover_image = Column(String)
    cover_path = Column(String)  # 新增：本地封面路径
    file_size = Column(BigInteger)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_scan_time = Column(DateTime)  # 新增：最后扫描时间
    is_active = Column(Integer, default=1)  # 新增：是否有效（1=有效，0=已删除）
    
    # 多对多标签关联
    tags = relationship("Tag", secondary="album_tags", backref="albums")
    
    def __repr__(self):
        return f"<Album(title='{self.title}', image_count={self.image_count})>"


# 用户表
class User(Base):
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