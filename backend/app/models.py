from sqlalchemy import Column, Integer, String, DateTime, BigInteger, ForeignKey, Table, LargeBinary, Float
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
    album_type = Column(String, default='cbz')  # 图集类型：'cbz' 或 'folder'
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


# 图集向量表（用于AI搜索）
class AlbumEmbedding(Base):
    __tablename__ = "album_embeddings"
    
    id = Column(Integer, primary_key=True)
    album_id = Column(Integer, ForeignKey('albums.id'), unique=True, nullable=False)
    embedding = Column(LargeBinary, nullable=False)  # 512维 float32 向量 = 2048 bytes
    model_version = Column(String, default='clip-v1')  # 模型版本
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联
    album = relationship("Album", backref="embedding")
    
    def __repr__(self):
        return f"<AlbumEmbedding(album_id={self.album_id}, model='{self.model_version}')>"


# AI扫描任务状态表
class AIScanTask(Base):
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


# 扫描任务状态表
class ScanTask(Base):
    __tablename__ = "scan_tasks"
    
    id = Column(Integer, primary_key=True)
    task_id = Column(String, unique=True, nullable=False)  # UUID
    status = Column(String, default='pending')  # pending, running, completed, failed
    scan_type = Column(String, default='incremental')  # incremental, full
    total_files = Column(Integer, default=0)
    processed_files = Column(Integer, default=0)
    new_albums = Column(Integer, default=0)
    updated_albums = Column(Integer, default=0)
    failed_files = Column(Integer, default=0)
    current_file = Column(String)
    error_message = Column(String)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ScanTask(task_id='{self.task_id}', status='{self.status}')>"