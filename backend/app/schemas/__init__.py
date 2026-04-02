"""
Schema 模块

导出所有 Pydantic Schema，保持向后兼容
"""
from .common import PagedResponse
from .tag import TagBase, TagResponse, OrganizationBase, OrganizationResponse, ModelBase, ModelResponse, CategoryTree
from .album import AlbumBase, AlbumCreate, AlbumSummary, AlbumResponse, ScanResponse
from .user import UserBase, UserResponse, UserLogin, Token

__all__ = [
    # Common
    'PagedResponse',
    # Tag
    'TagBase',
    'TagResponse',
    'OrganizationBase',
    'OrganizationResponse',
    'ModelBase',
    'ModelResponse',
    'CategoryTree',
    # Album
    'AlbumBase',
    'AlbumCreate',
    'AlbumSummary',
    'AlbumResponse',
    'ScanResponse',
    # User
    'UserBase',
    'UserResponse',
    'UserLogin',
    'Token',
]
