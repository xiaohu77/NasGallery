import logging
from pathlib import Path
from typing import Dict, Callable, Optional, Any
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


class ScanContext:
    """扫描上下文，包含扫描所需的所有组件"""
    
    def __init__(self, db: Session, scan_path: Path, use_lock: bool = True):
        from ..config import settings
        from .cache import cache_service
        
        self.db = db
        self.scan_path = scan_path
        self.settings = settings
        self.cache_service = cache_service
        self.cover_service = CoverService(settings.COVERS_DIR)
        self.scan_logger = ScanLogger()
        
        # 导入重构后的类
        from .scanner import (
            FileScanner,
            MetadataExtractor,
            DatabaseUpdater,
            CacheCleaner,
            StatsUpdater,
        )
        
        # 初始化各个组件
        self.file_scanner = FileScanner(scan_path, use_lock)
        self.metadata_extractor = MetadataExtractor()
        self.database_updater = DatabaseUpdater(db, self.scan_logger)
        self.cache_cleaner = CacheCleaner(db, self.scan_logger, cache_service, self.cover_service)
        self.stats_updater = StatsUpdater(db)
        
        # 扫描状态
        self.all_album_paths = set()
        self.total_items = 0
        self.processed_items = 0
    
    def acquire_lock(self) -> bool:
        """获取文件锁"""
        if not self.file_scanner.acquire_lock():
            self.scan_logger.log_error("全局", "扫描锁获取失败，可能有其他扫描任务正在进行")
            return False
        return True
    
    def release_lock(self):
        """释放文件锁"""
        self.file_scanner.release_lock()
        logger.info("🔒 释放扫描锁")
    
    def update_progress(self, current_file: str, progress_callback: Optional[Callable] = None):
        """更新进度"""
        self.processed_items += 1
        if progress_callback:
            progress_callback({
                'status': 'running',
                'type': 'album_scan',
                'total': self.total_items,
                'processed': self.processed_items,
                'progress': int(self.processed_items / self.total_items * 100) if self.total_items > 0 else 0,
                'current_file': current_file,
                'new_albums': self.scan_logger.results['new_albums'],
                'updated_albums': self.scan_logger.results['updated_albums']
            })


def _process_single_album(
    ctx: ScanContext,
    album_path: Path,
    album_type: str,
    progress_callback: Optional[Callable] = None
):
    """
    处理单个图集（CBZ或文件夹）
    
    Args:
        ctx: 扫描上下文
        album_path: 图集路径
        album_type: 图集类型 ('cbz' 或 'folder')
        progress_callback: 进度回调函数
    """
    db = ctx.db
    scan_logger = ctx.scan_logger
    metadata_extractor = ctx.metadata_extractor
    database_updater = ctx.database_updater
    cover_service = ctx.cover_service
    stats_updater = ctx.stats_updater
    scan_path = ctx.scan_path
    
    # 检查文件/文件夹是否存在
    if not album_path.exists():
        error_msg = "文件不存在" if album_type == 'cbz' else "文件夹不存在"
        scan_logger.log_error(album_path.name, error_msg)
        ctx.update_progress(album_path.name, progress_callback)
        return
    
    # 检查是否需要跳过
    if album_type == 'cbz':
        should_skip, reason = ctx.file_scanner.should_skip_file(album_path, db, Album)
    else:
        should_skip, reason = ctx.file_scanner.should_skip_folder(album_path, db, Album)
    
    if should_skip:
        scan_logger.log_skipped_file(album_path.name, reason)
        scan_logger.results['skipped_files'] += 1
        ctx.update_progress(album_path.name, progress_callback)
        return
    elif reason and "强制更新" in reason:
        scan_logger.log_warning(album_path.name, reason)
    
    scan_logger.results['scanned_files'] += 1
    
    # 提取元数据
    if album_type == 'cbz':
        metadata_json = metadata_extractor.extract_metadata_from_cbz(album_path)
        cbz_metadata = metadata_extractor.extract_cbz_metadata(album_path)
        metadata = cbz_metadata
    else:
        metadata_json = metadata_extractor.extract_metadata_from_folder(album_path)
        folder_metadata = metadata_extractor.extract_folder_metadata(album_path)
        metadata = folder_metadata
    
    # 解析标签信息
    tag_info = {}
    album_description = None
    
    # 从路径提取机构/模特信息
    relative_path = str(album_path.parent.relative_to(scan_path)) if album_type == 'cbz' else str(album_path.relative_to(scan_path))
    path_tags = metadata_extractor.parse_path_structure(relative_path, str(scan_path))
    
    if metadata_json:
        tag_info = metadata_extractor.parse_metadata_to_tags(metadata_json)
        for tag_type in ['org', 'model', 'cosplayer', 'character']:
            if path_tags.get(tag_type):
                tag_info[tag_type] = path_tags[tag_type]
        album_description = metadata_json.get('description')
        scan_logger.log_debug(f"使用metadata（标签从路径获取）: {album_path.name}")
    else:
        if album_type == 'cbz':
            filename_tags = metadata_extractor.parse_filename(album_path.name)
        else:
            filename_tags = metadata_extractor.parse_folder_name(album_path.name)
        tag_info = filename_tags
        for tag_type in ['org', 'model', 'cosplayer', 'character']:
            if path_tags.get(tag_type):
                tag_info[tag_type] = path_tags[tag_type]
        scan_logger.log_warning(album_path.name, "使用文件名解析（未找到metadata.json）")
    
    # 检查图片数量
    if metadata['image_count'] == 0:
        scan_logger.log_warning(album_path.name, "未找到图片文件")
    
    # 创建或更新专辑
    album = database_updater.create_or_update_album(
        album_path, metadata, tag_info, album_description, album_type=album_type
    )
    
    # 提取封面
    cover_image = metadata['cover_image']
    if not cover_image and metadata.get('image_list'):
        cover_image = metadata['image_list'][0]
        logger.debug(f"使用第一张图片作为封面: {album_path.name}")
    
    if cover_image:
        if album_type == 'cbz':
            cover_path = cover_service.extract_cover_to_folder(album_path, cover_image, album.id)
        else:
            cover_path = cover_service.extract_cover_from_folder(album_path, cover_image, album.id)
        
        if cover_path:
            album.cover_path = str(cover_path)
            logger.debug(f"封面已更新: {album.id}")
        else:
            scan_logger.log_warning(album_path.name, "封面生成失败")
    else:
        scan_logger.log_warning(album_path.name, "未找到任何图片")
    
    # 提交事务
    db.commit()
    
    # 增量更新统计信息
    stats_updater.update_stats_incremental(album, tag_info)
    
    # 更新进度
    ctx.update_progress(album_path.name, progress_callback)


def _cleanup_after_scan(ctx: ScanContext):
    """扫描完成后的清理工作"""
    db = ctx.db
    
    try:
        # 清理孤儿封面
        logger.info("🧹 清理孤儿封面...")
        ctx.cache_cleaner.cleanup_orphaned_covers(ctx.all_album_paths)
        
        # 清理孤立标签和关联
        logger.info("🏷️ 清理孤立标签...")
        cleanup_orphaned_data(db)
        
        # 最终统计信息校准
        logger.info("📊 校准统计信息...")
        ctx.stats_updater.update_statistics()
        db.commit()
        logger.info("✅ 统计信息已更新")
        
    except Exception as e:
        logger.error(f"清理过程失败: {e}")
        db.rollback()
        ctx.scan_logger.log_error("清理过程", str(e))
        ctx.scan_logger.results['errors'] += 1


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
    
    # 创建扫描上下文
    ctx = ScanContext(db, scan_path, use_lock)
    scan_logger = ctx.scan_logger
    
    # 获取文件锁
    if not ctx.acquire_lock():
        return scan_logger.get_summary()
    
    try:
        logger.info(f"🚀 开始扫描: {scan_path}")
        
        # 1. 扫描CBZ文件
        try:
            cbz_files, cbz_paths = ctx.file_scanner.scan_cbz_files()
        except Exception as e:
            scan_logger.log_error("CBZ扫描", f"无法访问目录: {e}")
            return scan_logger.get_summary()
        
        # 2. 扫描文件夹图集
        try:
            folder_albums, folder_paths = ctx.file_scanner.scan_folder_albums()
        except Exception as e:
            scan_logger.log_error("文件夹扫描", f"无法访问目录: {e}")
            return scan_logger.get_summary()
        
        # 合并所有图集路径
        ctx.all_album_paths = cbz_paths | folder_paths
        ctx.total_items = len(cbz_files) + len(folder_albums)
        
        # 3. 检测已删除的图集并清理缓存
        ctx.cache_cleaner.detect_deleted_albums(ctx.all_album_paths)
        
        # 4. 处理每个CBZ文件
        for cbz_file in cbz_files:
            try:
                _process_single_album(ctx, cbz_file, 'cbz', progress_callback)
            except Exception as e:
                scan_logger.log_error(cbz_file.name, str(e))
                db.rollback()
                ctx.update_progress(cbz_file.name, progress_callback)
        
        # 5. 处理每个文件夹图集
        for folder_path in folder_albums:
            try:
                _process_single_album(ctx, folder_path, 'folder', progress_callback)
            except Exception as e:
                scan_logger.log_error(folder_path.name, str(e))
                db.rollback()
                ctx.update_progress(folder_path.name, progress_callback)
        
        # 6. 清理工作
        _cleanup_after_scan(ctx)
        
        # 发送完成状态
        if progress_callback:
            progress_callback({
                'status': 'completed',
                'type': 'album_scan',
                'total': ctx.total_items,
                'processed': ctx.processed_items,
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
        
        if progress_callback:
            progress_callback({
                'status': 'failed',
                'type': 'album_scan',
                'error': str(e)
            })
    
    finally:
        ctx.release_lock()
    
    return scan_logger.get_summary()


def cleanup_deleted_albums(db: Session, days: int = 30, cache_service=None):
    """
    清理已删除超过指定天数的图集记录
    """
    from .scanner.album_cleaner import AlbumCleaner
    cleaner = AlbumCleaner(db)
    return cleaner.cleanup_deleted_albums(days, cache_service)


def cleanup_orphaned_data(db: Session):
    """
    清理孤儿数据（孤立的标签和关联）
    """
    from .scanner.album_cleaner import AlbumCleaner
    cleaner = AlbumCleaner(db)
    return cleaner.cleanup_orphaned_data()


def get_orphaned_stats(db: Session) -> Dict:
    """获取孤儿数据统计信息"""
    from .scanner.album_cleaner import AlbumCleaner
    cleaner = AlbumCleaner(db)
    return cleaner.get_orphaned_stats()


def get_scan_stats(db: Session) -> Dict:
    """获取扫描统计信息"""
    from .scanner.scan_stats import ScanStats
    stats = ScanStats(db)
    return stats.get_scan_stats()
