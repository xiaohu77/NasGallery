import logging
from pathlib import Path
from typing import Dict, Callable, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from ..models import Album, AlbumTag, Tag, Organization, Model
from .cover import CoverService

logger = logging.getLogger(__name__)


class ScanLogger:
    """扫描日志管理器"""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.results = {
            'scanned_files': 0,
            'new_albums': 0,
            'updated_albums': 0,
            'skipped_files': 0,
            'deleted_albums': 0,
            'errors': 0,
            'warnings': 0
        }
        self.details = {
            'new_files': [],
            'updated_files': [],
            'skipped_files': [],
            'deleted_albums': [],
            'errors': [],
            'warnings': []
        }
    
    def log_new_file(self, filename: str):
        self.details['new_files'].append(filename)
        logger.info(f"📦 新增图集: {filename}")
    
    def log_updated_file(self, filename: str):
        self.details['updated_files'].append(filename)
        logger.info(f"🔄 更新图集: {filename}")
    
    def log_skipped_file(self, filename: str, reason: str):
        self.details['skipped_files'].append(f"{filename} ({reason})")
        logger.info(f"⏭️  跳过文件: {filename} - {reason}")
    
    def log_deleted_album(self, album_id: int, title: str):
        self.details['deleted_albums'].append(f"ID:{album_id} - {title}")
        logger.info(f"🗑️  删除图集: ID:{album_id} - {title}")
    
    def log_error(self, filename: str, error: str):
        self.details['errors'].append(f"{filename}: {error}")
        logger.error(f"❌ 错误: {filename} - {error}")
        self.results['errors'] += 1
    
    def log_warning(self, filename: str, warning: str):
        self.details['warnings'].append(f"{filename}: {warning}")
        logger.warning(f"⚠️  警告: {filename} - {warning}")
        self.results['warnings'] += 1
    
    def log_debug(self, message: str):
        logger.debug(f"🔍 调试: {message}")
    
    def get_summary(self) -> Dict:
        duration = (datetime.utcnow() - self.start_time).total_seconds()
        summary = {
            'duration_seconds': round(duration, 2),
            'results': self.results,
            'details': self.details
        }
        logger.info(f"📊 扫描完成: {self.results} (耗时: {duration:.2f}s)")
        return summary


def scan_albums(db: Session, scan_path: Path = None, use_lock: bool = True, progress_callback: Optional[Callable] = None) -> Dict:
    """
    扫描目录并更新数据库（支持CBZ和文件夹图集）
    
    Args:
        db: 数据库会话
        scan_path: 扫描路径
        use_lock: 是否使用文件锁防止并发扫描
        progress_callback: 进度回调函数
    
    Returns:
        扫描结果和详细日志
    """
    if scan_path is None:
        from ..config import settings
        scan_path = settings.IMAGES_DIR
    else:
        from ..config import settings
    
    from .cache import cache_service
    from .archive import FolderArchiveService
    cover_service = CoverService(settings.COVERS_DIR)
    scan_logger = ScanLogger()
    
    # 导入重构后的类
    from .scanner import (
        FileScanner,
        MetadataExtractor,
        DatabaseUpdater,
        CacheCleaner,
        StatsUpdater,
    )
    
    # 初始化各个组件
    file_scanner = FileScanner(scan_path, use_lock)
    metadata_extractor = MetadataExtractor()
    database_updater = DatabaseUpdater(db, scan_logger)
    cache_cleaner = CacheCleaner(db, scan_logger, cache_service, cover_service)
    stats_updater = StatsUpdater(db)
    
    # 获取文件锁
    if not file_scanner.acquire_lock():
        scan_logger.log_error("全局", "扫描锁获取失败，可能有其他扫描任务正在进行")
        return scan_logger.get_summary()
    
    try:
        logger.info(f"🚀 开始扫描: {scan_path}")
        
        # 1. 扫描CBZ文件
        try:
            cbz_files, cbz_paths = file_scanner.scan_cbz_files()
        except Exception as e:
            scan_logger.log_error("CBZ扫描", f"无法访问目录: {e}")
            return scan_logger.get_summary()
        
        # 2. 扫描文件夹图集
        try:
            folder_albums, folder_paths = file_scanner.scan_folder_albums()
        except Exception as e:
            scan_logger.log_error("文件夹扫描", f"无法访问目录: {e}")
            return scan_logger.get_summary()
        
        # 合并所有图集路径
        all_album_paths = cbz_paths | folder_paths
        total_items = len(cbz_files) + len(folder_albums)
        processed_items = 0
        
        # 3. 检测已删除的图集并清理缓存
        cache_cleaner.detect_deleted_albums(all_album_paths)
        
        # 4. 处理每个CBZ文件
        for cbz_file in cbz_files:
            try:
                # 检查文件是否存在
                if not cbz_file.exists():
                    scan_logger.log_error(cbz_file.name, "文件不存在")
                    processed_items += 1
                    continue
                
                # 检查是否需要跳过
                should_skip, reason = file_scanner.should_skip_file(cbz_file, db, Album)
                if should_skip:
                    scan_logger.log_skipped_file(cbz_file.name, reason)
                    scan_logger.results['skipped_files'] += 1
                    processed_items += 1
                    continue
                elif reason == "文件大小变化，强制更新":
                    scan_logger.log_warning(cbz_file.name, reason)
                
                scan_logger.results['scanned_files'] += 1
                
                # 提取元数据
                metadata_json = metadata_extractor.extract_metadata_from_cbz(cbz_file)
                
                tag_info = {}
                album_title = cbz_file.stem
                album_description = None
                
                if metadata_json:
                    # 使用metadata.json的数据，但模特字段从文件名获取
                    tag_info = metadata_extractor.parse_metadata_to_tags(metadata_json)
                    # 重新从文件名解析模特字段
                    filename_tags = metadata_extractor.parse_filename(cbz_file.name)
                    tag_info['model'] = filename_tags['model']
                    
                    album_title = metadata_json.get('title', cbz_file.stem)
                    album_description = metadata_json.get('description')
                    scan_logger.log_debug(f"使用metadata（模特从文件名获取）: {cbz_file.name}")
                else:
                    # 降级使用文件名解析
                    tag_info = metadata_extractor.parse_filename(cbz_file.name)
                    scan_logger.log_warning(cbz_file.name, "使用文件名解析（未找到metadata.json）")
                
                # 提取CBZ文件的图片元数据
                cbz_metadata = metadata_extractor.extract_cbz_metadata(cbz_file)
                
                if cbz_metadata['image_count'] == 0:
                    scan_logger.log_warning(cbz_file.name, "未找到图片文件")
                
                # 创建或更新专辑
                album = database_updater.create_or_update_album(
                    cbz_file, cbz_metadata, tag_info, album_description, album_type='cbz'
                )
                
                # 提取封面
                if cbz_metadata['cover_image']:
                    cover_path = cover_service.extract_cover_to_folder(
                        cbz_file, cbz_metadata['cover_image'], album.id
                    )
                    if cover_path:
                        album.cover_path = str(cover_path)
                        logger.debug(f"封面已更新: {album.id}")
                
                # 每个图集处理完成后立即提交，使数据实时可用
                db.commit()
                
                # 增量更新统计信息（只更新当前图集涉及的分类）
                stats_updater.update_stats_incremental(album, tag_info)
                
                # 更新进度
                processed_items += 1
                if progress_callback:
                    progress_callback({
                        'status': 'running',
                        'type': 'album_scan',
                        'total': total_items,
                        'processed': processed_items,
                        'progress': int(processed_items / total_items * 100) if total_items > 0 else 0,
                        'current_file': cbz_file.name,
                        'new_albums': scan_logger.results['new_albums'],
                        'updated_albums': scan_logger.results['updated_albums']
                    })
                
            except Exception as e:
                scan_logger.log_error(cbz_file.name, str(e))
                processed_items += 1
                continue
        
        # 5. 处理每个文件夹图集
        for folder_path in folder_albums:
            try:
                # 检查文件夹是否存在
                if not folder_path.exists():
                    scan_logger.log_error(folder_path.name, "文件夹不存在")
                    processed_items += 1
                    continue
                
                # 检查是否需要跳过
                should_skip, reason = file_scanner.should_skip_folder(folder_path, db, Album)
                if should_skip:
                    scan_logger.log_skipped_file(folder_path.name, reason)
                    scan_logger.results['skipped_files'] += 1
                    processed_items += 1
                    continue
                elif reason == "文件夹内容变化，强制更新":
                    scan_logger.log_warning(folder_path.name, reason)
                
                scan_logger.results['scanned_files'] += 1
                
                # 提取元数据（优先从metadata.json，降级使用文件夹名）
                metadata_json = metadata_extractor.extract_metadata_from_folder(folder_path)
                
                tag_info = {}
                album_title = folder_path.name
                album_description = None
                
                if metadata_json:
                    # 使用metadata.json的数据
                    tag_info = metadata_extractor.parse_metadata_to_tags(metadata_json)
                    album_title = metadata_json.get('title', folder_path.name)
                    album_description = metadata_json.get('description')
                    scan_logger.log_debug(f"使用metadata: {folder_path.name}")
                else:
                    # 降级使用文件夹名解析
                    tag_info = metadata_extractor.parse_folder_name(folder_path.name)
                    scan_logger.log_warning(folder_path.name, "使用文件夹名解析（未找到metadata.json）")
                
                # 提取文件夹图集的图片元数据
                folder_metadata = metadata_extractor.extract_folder_metadata(folder_path)
                
                if folder_metadata['image_count'] == 0:
                    scan_logger.log_warning(folder_path.name, "未找到图片文件")
                
                # 创建或更新专辑
                album = database_updater.create_or_update_album(
                    folder_path, folder_metadata, tag_info, album_description, album_type='folder'
                )
                
                # 提取封面
                if folder_metadata['cover_image']:
                    cover_path = cover_service.extract_cover_from_folder(
                        folder_path, folder_metadata['cover_image'], album.id
                    )
                    if cover_path:
                        album.cover_path = str(cover_path)
                        logger.debug(f"封面已更新: {album.id}")
                
                # 每个图集处理完成后立即提交，使数据实时可用
                db.commit()
                
                # 增量更新统计信息（只更新当前图集涉及的分类）
                stats_updater.update_stats_incremental(album, tag_info)
                
                # 更新进度
                processed_items += 1
                if progress_callback:
                    progress_callback({
                        'status': 'running',
                        'type': 'album_scan',
                        'total': total_items,
                        'processed': processed_items,
                        'progress': int(processed_items / total_items * 100) if total_items > 0 else 0,
                        'current_file': folder_path.name,
                        'new_albums': scan_logger.results['new_albums'],
                        'updated_albums': scan_logger.results['updated_albums']
                    })
                
            except Exception as e:
                scan_logger.log_error(folder_path.name, str(e))
                processed_items += 1
                continue
        
        # 6. 清理已删除图集的封面
        try:
            logger.info("🧹 清理孤儿封面...")
            cache_cleaner.cleanup_orphaned_covers(all_album_paths)
            
            # 7. 最终统计信息校准（处理可能遗漏的统计）
            logger.info("📊 校准统计信息...")
            stats_updater.update_statistics()
            db.commit()
            logger.info("✅ 统计信息已更新")
            
        except Exception as e:
            logger.error(f"数据库提交失败: {e}")
            db.rollback()
            scan_logger.log_error("数据库提交", str(e))
            scan_logger.results['errors'] += 1
        
        # 发送完成状态
        if progress_callback:
            summary = scan_logger.get_summary()
            progress_callback({
                'status': 'completed',
                'type': 'album_scan',
                'total': total_items,
                'processed': processed_items,
                'progress': 100,
                'new_albums': scan_logger.results['new_albums'],
                'updated_albums': scan_logger.results['updated_albums'],
                'skipped_files': scan_logger.results['skipped_files'],
                'errors': scan_logger.results['errors']
            })
        
    except Exception as e:
        logger.error(f"扫描过程异常: {e}")
        scan_logger.log_error("扫描过程", str(e))
        db.rollback()
        
        # 发送失败状态
        if progress_callback:
            progress_callback({
                'status': 'failed',
                'type': 'album_scan',
                'error': str(e)
            })
    
    finally:
        # 释放文件锁
        file_scanner.release_lock()
        logger.info("🔒 释放扫描锁")
    
    return scan_logger.get_summary()


def cleanup_deleted_albums(db: Session, days: int = 30, cache_service=None):
    """
    清理已删除超过指定天数的图集记录
    
    Args:
        db: 数据库会话
        days: 删除超过多少天的记录
        cache_service: 缓存服务实例
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # 查找已删除且超过保留期限的图集
        albums_to_delete = db.query(Album).filter(
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
            db.query(AlbumTag).filter(AlbumTag.album_id == album.id).delete()
            
            # 删除图集记录
            db.delete(album)
            deleted_count += 1
            
            logger.info(f"清理图集: ID:{album.id} - {album.title}")
        
        db.commit()
        logger.info(f"✅ 清理完成，删除 {deleted_count} 个过期图集记录")
        
    except Exception as e:
        logger.error(f"清理失败: {e}")
        db.rollback()
        raise


def cleanup_orphaned_data(db: Session):
    """
    清理孤儿数据（孤立的标签和关联）
    包括：已删除图集的关联、没有关联任何图集的标签
    """
    try:
        # 1. 删除已删除图集的标签关联
        orphaned_album_tags = db.query(AlbumTag).filter(
            AlbumTag.album_id.in_(
                db.query(Album.id).filter(Album.is_active == 0)
            )
        ).all()
        
        deleted_album_tags = 0
        for album_tag in orphaned_album_tags:
            db.delete(album_tag)
            deleted_album_tags += 1
        
        if deleted_album_tags > 0:
            logger.info(f"🗑️ 删除 {deleted_album_tags} 个孤儿图集标签关联")
        
        # 2. 删除孤立的标签（没有关联任何有效图集的标签）
        # 先获取所有被使用的标签ID
        used_tag_ids = set(
            t[0] for t in db.query(AlbumTag.tag_id)
            .join(Album)
            .filter(Album.is_active == 1)
            .distinct()
            .all()
        )
        
        # 查找孤立的标签（排除套图和模特的标签，因为它们可能有独立存在价值）
        orphan_tags = db.query(Tag).filter(
            Tag.id.notin_(used_tag_ids),
            Tag.type == 'tag'  # 只清理通用标签，不清理套图和模特标签
        ).all()
        
        deleted_tags = 0
        for tag in orphan_tags:
            logger.info(f"🗑️ 删除孤立标签: {tag.name} (ID:{tag.id})")
            db.delete(tag)
            deleted_tags += 1
        
        # 3. 清理孤立的套图和模特（如果它们的标签没有关联任何图集）
        orphan_orgs = db.query(Organization).filter(
            ~Organization.tag.has(
                Tag.albums.any(Album.is_active == 1)
            )
        ).all()
        
        deleted_orgs = 0
        for org in orphan_orgs:
            logger.info(f"🗑️ 删除孤立套图: {org.name} (ID:{org.id})")
            db.delete(org)
            deleted_orgs += 1
        
        orphan_models = db.query(Model).filter(
            ~Model.tag.has(
                Tag.albums.any(Album.is_active == 1)
            )
        ).all()
        
        deleted_models = 0
        for model in orphan_models:
            logger.info(f"🗑️ 删除孤立模特: {model.name} (ID:{model.id})")
            db.delete(model)
            deleted_models += 1
        
        db.commit()
        
        total_deleted = deleted_album_tags + deleted_tags + deleted_orgs + deleted_models
        if total_deleted > 0:
            logger.info(f"✅ 孤儿数据清理完成，共删除 {total_deleted} 条记录")
        else:
            logger.info("✅ 没有发现孤儿数据")
        
    except Exception as e:
        logger.error(f"清理孤儿数据失败: {e}")
        db.rollback()
        raise


def get_orphaned_stats(db: Session) -> Dict:
    """获取孤儿数据统计信息"""
    try:
        from sqlalchemy import func
        
        # 已删除图集的标签关联数
        orphaned_album_tags = db.query(AlbumTag).filter(
            AlbumTag.album_id.in_(
                db.query(Album.id).filter(Album.is_active == 0)
            )
        ).count()
        
        # 孤立的通用标签数
        used_tag_ids = set(
            t[0] for t in db.query(AlbumTag.tag_id)
            .join(Album)
            .filter(Album.is_active == 1)
            .distinct()
            .all()
        )
        
        orphan_tags = db.query(Tag).filter(
            Tag.id.notin_(used_tag_ids) if used_tag_ids else True,
            Tag.type == 'tag'
        ).count()
        
        # 孤立的套图数
        orphan_orgs = db.query(Organization).filter(
            ~Organization.tag.has(
                Tag.albums.any(Album.is_active == 1)
            )
        ).count()
        
        # 孤立的模特数
        orphan_models = db.query(Model).filter(
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


def get_scan_stats(db: Session) -> Dict:
    """获取扫描统计信息"""
    try:
        from sqlalchemy import func
        
        total_albums = db.query(Album).filter(Album.is_active == 1).count()
        
        total_images = db.query(Album).filter(Album.is_active == 1).with_entities(
            func.sum(Album.image_count)
        ).scalar() or 0
        
        total_size = db.query(Album).filter(Album.is_active == 1).with_entities(
            func.sum(Album.file_size)
        ).scalar() or 0
        
        # 按最后扫描时间分组
        recent_scans = db.query(Album).filter(
            Album.is_active == 1,
            Album.last_scan_time > datetime.utcnow().replace(hour=0, minute=0, second=0)
        ).count()
        
        return {
            'total_albums': total_albums,
            'total_images': total_images,
            'total_size_mb': round(total_size / 1024 / 1024, 2),
            'recent_scans_today': recent_scans,
            'organizations': db.query(Organization).count(),
            'models': db.query(Model).count(),
            'tags': db.query(Tag).count()
        }
    except Exception as e:
        logger.error(f"获取统计失败: {e}")
        return {}
