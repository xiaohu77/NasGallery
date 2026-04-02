"""
扫描统计服务模块

处理扫描统计相关的功能：
- 获取扫描统计信息
- 更新统计信息
"""
import logging
from datetime import datetime
from typing import Dict
from sqlalchemy.orm import Session
from sqlalchemy import func

from ...models import Album, Tag, Organization, Model

logger = logging.getLogger(__name__)


class ScanStats:
    """扫描统计服务"""
    
    def __init__(self, db: Session):
        """
        初始化扫描统计服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def get_scan_stats(self) -> Dict:
        """
        获取扫描统计信息
        
        Returns:
            扫描统计信息
        """
        try:
            total_albums = self.db.query(Album).filter(Album.is_active == 1).count()
            
            total_images = self.db.query(Album).filter(Album.is_active == 1).with_entities(
                func.sum(Album.image_count)
            ).scalar() or 0
            
            total_size = self.db.query(Album).filter(Album.is_active == 1).with_entities(
                func.sum(Album.file_size)
            ).scalar() or 0
            
            # 按最后扫描时间分组
            recent_scans = self.db.query(Album).filter(
                Album.is_active == 1,
                Album.last_scan_time > datetime.utcnow().replace(hour=0, minute=0, second=0)
            ).count()
            
            return {
                'total_albums': total_albums,
                'total_images': total_images,
                'total_size_mb': round(total_size / 1024 / 1024, 2),
                'recent_scans_today': recent_scans,
                'organizations': self.db.query(Organization).count(),
                'models': self.db.query(Model).count(),
                'tags': self.db.query(Tag).count()
            }
        except Exception as e:
            logger.error(f"获取统计失败: {e}")
            return {}
    
    def get_storage_stats(self) -> Dict:
        """
        获取存储统计信息
        
        Returns:
            存储统计信息
        """
        try:
            # CBZ 文件统计
            cbz_stats = self.db.query(
                func.count(Album.id).label('count'),
                func.sum(Album.file_size).label('total_size')
            ).filter(
                Album.is_active == 1,
                Album.album_type == 'cbz'
            ).first()
            
            # 文件夹图集统计
            folder_stats = self.db.query(
                func.count(Album.id).label('count'),
                func.sum(Album.file_size).label('total_size')
            ).filter(
                Album.is_active == 1,
                Album.album_type == 'folder'
            ).first()
            
            return {
                'cbz': {
                    'count': cbz_stats.count or 0,
                    'total_size_mb': round((cbz_stats.total_size or 0) / 1024 / 1024, 2)
                },
                'folder': {
                    'count': folder_stats.count or 0,
                    'total_size_mb': round((folder_stats.total_size or 0) / 1024 / 1024, 2)
                }
            }
        except Exception as e:
            logger.error(f"获取存储统计失败: {e}")
            return {}
