"""
通用工具函数
"""
from pathlib import Path
from typing import Optional, List, Tuple, Any
from sqlalchemy.orm import Query

from app.models import Album


def get_cover_url(album: Album) -> Optional[str]:
    """
    获取图集封面URL
    
    Args:
        album: 图集对象
        
    Returns:
        封面URL，如果没有封面返回None
    """
    if album.cover_path:
        return f"/covers/{Path(album.cover_path).name}"
    elif album.cover_image:
        return f"/albums/{album.id}/images/{album.cover_image}"
    return None


def paginate(query: Query, page: int, size: int) -> Tuple[int, List[Any]]:
    """
    分页查询
    
    Args:
        query: SQLAlchemy查询对象
        page: 页码（从1开始）
        size: 每页数量
        
    Returns:
        (总数, 当前页数据列表)
    """
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return total, items
