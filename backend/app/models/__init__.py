"""
数据模型模块

导出所有 SQLAlchemy 模型，保持向后兼容
"""
from .base import Base
from .album import Album, AlbumTag
from .tag import Tag, Organization, Model
from .user import User
from .user_extra import UserFavorite, UserHistory
from .ai import AlbumEmbedding, AIScanTask
from .task import ScanTask

__all__ = [
    'Base',
    'Album',
    'AlbumTag',
    'Tag',
    'Organization',
    'Model',
    'User',
    'UserFavorite',
    'UserHistory',
    'AlbumEmbedding',
    'AIScanTask',
    'ScanTask',
]
