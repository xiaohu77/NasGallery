from .file_scanner import FileScanner
from .metadata_extractor import MetadataExtractor
from .database_updater import DatabaseUpdater
from .cache_cleaner import CacheCleaner
from .stats_updater import StatsUpdater
from .album_cleaner import AlbumCleaner
from .scan_stats import ScanStats

# 导入 scanner_main 中的函数和类
from ..scanner_main import (
    ScanLogger,
    scan_albums,
    cleanup_deleted_albums,
    cleanup_orphaned_data,
    get_orphaned_stats,
    get_scan_stats,
)

__all__ = [
    # 类
    'FileScanner',
    'MetadataExtractor',
    'DatabaseUpdater',
    'CacheCleaner',
    'StatsUpdater',
    'AlbumCleaner',
    'ScanStats',
    # 函数（向后兼容）
    'ScanLogger',
    'scan_albums',
    'cleanup_deleted_albums',
    'cleanup_orphaned_data',
    'get_orphaned_stats',
    'get_scan_stats',
]
