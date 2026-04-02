"""
图集清理服务模块

处理图集清理相关的功能：
- 清理已删除超过指定天数的图集记录
- 清理孤儿数据（孤立的标签和关联）
- 获取孤儿数据统计信息
"""
import logging
from datetime import datetime, timedelta
from typing import Dict
from sqlalchemy.orm import Session

from ...models import Album, AlbumTag, Tag, Organization, Model

logger = logging.getLogger(__name__)


class AlbumCleaner:
    """图集清理服务"""
    
    def __init__(self, db: Session):
        """
        初始化图集清理服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def cleanup_deleted_albums(self, days: int = 30, cache_service=None) -> int:
        """
        清理已删除超过指定天数的图集记录
        
        Args:
            days: 删除超过多少天的记录
            cache_service: 缓存服务实例
            
        Returns:
            删除的图集数量
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # 查找已删除且超过保留期限的图集
            albums_to_delete = self.db.query(Album).filter(
                Album.is_active == 0,
                Album.updated_at < cutoff_date
            ).all()
            
            deleted_count = 0
            for album in albums_to_delete:
                # 清理缓存文件
                if cache_service:
                    try:
                        cache_service.clear_album_image_list(album.id)
                        cache_service.clear_album_extracted_images(album.id)
                        cache_service.clear_album_metadata(album.id)
                        logger.debug(f"已清理图集 {album.id} 的缓存文件")
                    except Exception as e:
                        logger.warning(f"清理图集 {album.id} 缓存失败: {e}")
                
                # 删除标签关联
                self.db.query(AlbumTag).filter(AlbumTag.album_id == album.id).delete()
                
                # 删除图集记录
                self.db.delete(album)
                deleted_count += 1
                
                logger.info(f"清理图集: ID:{album.id} - {album.title}")
            
            self.db.commit()
            logger.info(f"✅ 清理完成，删除 {deleted_count} 个过期图集记录")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"清理失败: {e}")
            self.db.rollback()
            raise
    
    def cleanup_orphaned_data(self) -> Dict[str, int]:
        """
        清理孤儿数据（孤立的标签和关联）
        包括：已删除图集的关联、没有关联任何图集的标签
        
        Returns:
            清理统计信息
        """
        try:
            stats = {
                'deleted_album_tags': 0,
                'deleted_tags': 0,
                'deleted_orgs': 0,
                'deleted_models': 0
            }
            
            # 1. 删除已删除图集的标签关联
            orphaned_album_tags = self.db.query(AlbumTag).filter(
                AlbumTag.album_id.in_(
                    self.db.query(Album.id).filter(Album.is_active == 0)
                )
            ).all()
            
            for album_tag in orphaned_album_tags:
                self.db.delete(album_tag)
                stats['deleted_album_tags'] += 1
            
            if stats['deleted_album_tags'] > 0:
                logger.info(f"🗑️ 删除 {stats['deleted_album_tags']} 个孤儿图集标签关联")
            
            # 2. 删除孤立的标签（没有关联任何有效图集的标签）
            used_tag_ids = set(
                t[0] for t in self.db.query(AlbumTag.tag_id)
                .join(Album)
                .filter(Album.is_active == 1)
                .distinct()
                .all()
            )
            
            orphan_tags = self.db.query(Tag).filter(
                Tag.id.notin_(used_tag_ids) if used_tag_ids else True,
                Tag.type == 'tag'
            ).all()
            
            for tag in orphan_tags:
                logger.info(f"🗑️ 删除孤立标签: {tag.name} (ID:{tag.id})")
                self.db.delete(tag)
                stats['deleted_tags'] += 1
            
            # 3. 清理孤立的套图和模特
            orphan_orgs = self.db.query(Organization).filter(
                ~Organization.tag.has(
                    Tag.albums.any(Album.is_active == 1)
                )
            ).all()
            
            for org in orphan_orgs:
                logger.info(f"🗑️ 删除孤立套图: {org.name} (ID:{org.id})")
                self.db.delete(org)
                stats['deleted_orgs'] += 1
            
            orphan_models = self.db.query(Model).filter(
                ~Model.tag.has(
                    Tag.albums.any(Album.is_active == 1)
                )
            ).all()
            
            for model in orphan_models:
                logger.info(f"🗑️ 删除孤立模特: {model.name} (ID:{model.id})")
                self.db.delete(model)
                stats['deleted_models'] += 1
            
            self.db.commit()
            
            total_deleted = sum(stats.values())
            if total_deleted > 0:
                logger.info(f"✅ 孤儿数据清理完成，共删除 {total_deleted} 条记录")
            else:
                logger.info("✅ 没有发现孤儿数据")
            
            return stats
            
        except Exception as e:
            logger.error(f"清理孤儿数据失败: {e}")
            self.db.rollback()
            raise
    
    def get_orphaned_stats(self) -> Dict[str, int]:
        """
        获取孤儿数据统计信息
        
        Returns:
            孤儿数据统计
        """
        try:
            # 已删除图集的标签关联数
            orphaned_album_tags = self.db.query(AlbumTag).filter(
                AlbumTag.album_id.in_(
                    self.db.query(Album.id).filter(Album.is_active == 0)
                )
            ).count()
            
            # 孤立的通用标签数
            used_tag_ids = set(
                t[0] for t in self.db.query(AlbumTag.tag_id)
                .join(Album)
                .filter(Album.is_active == 1)
                .distinct()
                .all()
            )
            
            orphan_tags = self.db.query(Tag).filter(
                Tag.id.notin_(used_tag_ids) if used_tag_ids else True,
                Tag.type == 'tag'
            ).count()
            
            # 孤立的套图数
            orphan_orgs = self.db.query(Organization).filter(
                ~Organization.tag.has(
                    Tag.albums.any(Album.is_active == 1)
                )
            ).count()
            
            # 孤立的模特数
            orphan_models = self.db.query(Model).filter(
                ~Model.tag.has(
                    Tag.albums.any(Album.is_active == 1)
                )
            ).count()
            
            return {
                'orphaned_album_tags': orphaned_album_tags,
                'orphan_tags': orphan_tags,
                'orphan_orgs': orphan_orgs,
                'orphan_models': orphan_models,
                'total_orphans': orphaned_album_tags + orphan_tags + orphan_orgs + orphan_models
            }
        except Exception as e:
            logger.error(f"获取孤儿数据统计失败: {e}")
            return {}
