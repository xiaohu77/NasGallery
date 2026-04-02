"""
通用 Schema
"""
from pydantic import BaseModel
from typing import List, Any


class PagedResponse(BaseModel):
    """分页响应模型"""
    total: int
    page: int
    size: int
    items: List[Any]
