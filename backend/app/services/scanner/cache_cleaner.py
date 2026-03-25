import logging
from datetime import datetime
from typing import Set
from sqlalchemy.orm import Session

from ...models import Album

logger = logging.getLogger(__name__)


class CacheCleaner:
    """缓存清理和孤儿数据检测器"""
    
    def __init__(self, db: Session, scan_logger, cache_service, cover_service):
        """
        初始化缓存清理器
        
        Args:
            db: 数据库会话
            scan_logger: 扫描日志管理器
            cache_service: 缓存服务实例
            cover_service: 封面服务实例
        """
        self.db = db
        self.scan_logger = scan_logger
        self.cache_service = cache_service
        self.cover_service = cover_service
    
    def detect_deleted_albums(self, existing_files: Set[str]):
        """
        检测并标记已删除的图集，同时清理缓存
        
        Args:
            existing_files: 现有的图集路径集合（包含CBZ文件路径和文件夹路径）
        """
        try:
            # 查找数据库中所有有效图集
            albums = self.db.query(Album).filter(Album.is_active == 1).all()
            
            deleted_count = 0
            for album in albums:
                if album.file_path not in existing_files:
                    # 标记为已删除
                    album.is_active = 0
                    album.updated_at = datetime.utcnow()
                    self.scan_logger.log_deleted_album(album.id, album.title)
                    deleted_count += 1
                    
                    # 清理对应的缓存文件
                    if self.cache_service:
                        try:
                            # 清理图片列表缓存
                            self.cache_service.clear_album_image_list(album.id)
                            # 清理提取图片缓存
                            self.cache_service.clear_album_extracted_images(album.id)
                            # 清理元数据缓存
                            self.cache_service.clear_album_metadata(album.id)
                            logger.debug(f"已清理图集 {album.id} 的缓存文件")
                        except Exception as e:
                            logger.warning(f"清理图集 {album.id} 缓存失败: {e}")
            
            if deleted_count > 0:
                logger.info(f"检测到 {deleted_count} 个已删除的图集，并清理对应缓存")
                
        except Exception as e:
            logger.error(f"检测删除图集失败: {e}")
            raise
    
    def cleanup_orphaned_covers(self, valid_album_paths: Set[str]):
        """
        清理已删除图集的封面
        
        Args:
            valid_album_paths: 有效的图集路径集合（包含CBZ文件路径和文件夹路径）
        """
        if self.cover_service:
            self.cover_service.cleanup_orphaned_covers(valid_album_paths)
