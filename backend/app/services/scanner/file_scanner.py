import fcntl
import os
import logging
from pathlib import Path
from typing import List, Set, Tuple, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class FileScanner:
    """文件扫描和文件锁管理器"""
    
    def __init__(self, scan_path: Path, use_lock: bool = True):
        """
        初始化文件扫描器
        
        Args:
            scan_path: 扫描路径
            use_lock: 是否使用文件锁防止并发扫描
        """
        self.scan_path = scan_path
        self.use_lock = use_lock
        self.lock_file = Path("/tmp/nasgallery_scan.lock")
        self.lock_fd: Optional[int] = None
    
    def acquire_lock(self) -> bool:
        """
        获取文件锁
        
        Returns:
            是否成功获取锁
        """
        if not self.use_lock:
            return True
        
        try:
            self.lock_file.parent.mkdir(parents=True, exist_ok=True)
            self.lock_fd = os.open(self.lock_file, os.O_WRONLY | os.O_CREAT)
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            logger.debug("文件锁已获取")
            return True
        except (IOError, BlockingIOError, PermissionError):
            logger.error("扫描正在进行中，请稍后再试")
            return False
    
    def release_lock(self):
        """释放文件锁"""
        if self.lock_fd and self.use_lock:
            try:
                fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
                os.close(self.lock_fd)
                if self.lock_file.exists():
                    self.lock_file.unlink()
                logger.debug("文件锁已释放")
            except Exception as e:
                logger.warning(f"释放文件锁失败: {e}")
            finally:
                self.lock_fd = None
    
    def scan_cbz_files(self) -> Tuple[List[Path], Set[str]]:
        """
        扫描目录获取CBZ文件列表
        
        Returns:
            (CBZ文件路径列表, CBZ文件路径集合)
        
        Raises:
            Exception: 扫描失败时抛出异常
        """
        try:
            cbz_files = []
            
            # 使用 os.walk 并启用跟随软连接
            for root, dirs, files in os.walk(self.scan_path, followlinks=True):
                for file in files:
                    if file.endswith('.cbz'):
                        file_path = Path(root) / file
                        cbz_files.append(file_path)
            
            # 按文件修改时间从前到后排序（最旧的文件在前）
            # 这样确保新增文件按修改时间顺序依次入库，最新的文件入库时间也是最新的
            cbz_files.sort(key=lambda f: f.stat().st_mtime)
            
            existing_files = {str(f) for f in cbz_files}
            logger.info(f"📁 发现 {len(cbz_files)} 个CBZ文件（包括软连接中的内容），已按修改时间排序")
            
            return cbz_files, existing_files
            
        except Exception as e:
            logger.error(f"扫描目录失败: {e}")
            raise
    
    def scan_folder_albums(self) -> Tuple[List[Path], Set[str]]:
        """
        扫描目录获取文件夹图集列表
        
        文件夹图集判断规则：
        1. 目录必须包含至少一个图片文件（.jpg, .png, .jpeg）
        2. 忽略以 . 开头的隐藏目录
        3. 支持软链接
        
        Returns:
            (文件夹路径列表, 所有图集路径集合(CBZ+文件夹))
        """
        try:
            folder_albums = []
            all_album_paths = set()
            
            # 首先获取CBZ文件集合
            cbz_files = []
            for root, dirs, files in os.walk(self.scan_path, followlinks=True):
                for file in files:
                    if file.endswith('.cbz'):
                        file_path = Path(root) / file
                        cbz_files.append(file_path)
                        all_album_paths.add(str(file_path))
            
            # 扫描文件夹图集
            for root, dirs, files in os.walk(self.scan_path, followlinks=True):
                # 过滤掉隐藏目录
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for dir_name in dirs:
                    dir_path = Path(root) / dir_name
                    
                    # 检查目录是否包含图片文件
                    if self._is_valid_folder_album(dir_path):
                        folder_albums.append(dir_path)
                        all_album_paths.add(str(dir_path))
            
            # 按修改时间排序
            folder_albums.sort(key=lambda f: f.stat().st_mtime)
            
            logger.info(f"📁 发现 {len(folder_albums)} 个文件夹图集（共 {len(cbz_files)} 个CBZ文件）")
            
            return folder_albums, all_album_paths
            
        except Exception as e:
            logger.error(f"扫描文件夹图集失败: {e}")
            raise
    
    def _is_valid_folder_album(self, folder_path: Path) -> bool:
        """
        判断文件夹是否是有效的图集
        
        Args:
            folder_path: 文件夹路径
            
        Returns:
            是否是有效的图集
        """
        try:
            if not folder_path.is_dir():
                return False
            
            # 检查是否包含图片文件
            image_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
            for item in folder_path.iterdir():
                if item.is_file() and item.suffix.lower() in image_extensions:
                    return True
            
            return False
            
        except Exception as e:
            logger.warning(f"检查文件夹图集失败 {folder_path}: {e}")
            return False
    
    def should_skip_file(self, cbz_file: Path, db, Album) -> Tuple[bool, str]:
        """
        检查文件是否需要跳过（文件未修改）
        
        Returns:
            (是否跳过, 跳过原因)
        """
        try:
            # 获取文件信息
            file_stat = cbz_file.stat()
            file_mtime = file_stat.st_mtime
            file_size = file_stat.st_size
            file_mtime_dt = datetime.fromtimestamp(file_mtime)
            
            # 查询数据库中的专辑
            album = db.query(Album).filter(
                Album.file_path == str(cbz_file),
                Album.is_active == 1
            ).first()
            
            if album and album.last_scan_time and album.last_scan_time > file_mtime_dt:
                if file_size == album.file_size:  # 文件大小也相同才跳过
                    return True, "文件未修改"
                else:
                    return False, "文件大小变化，强制更新"
            
            return False, ""
            
        except Exception as e:
            logger.error(f"检查文件跳过状态失败 {cbz_file.name}: {e}")
            return False, ""
    
    def should_skip_folder(self, folder_path: Path, db, Album) -> Tuple[bool, str]:
        """
        检查文件夹图集是否需要跳过（文件夹未修改）
        
        Returns:
            (是否跳过, 跳过原因)
        """
        try:
            # 获取文件夹信息（使用文件夹的修改时间）
            folder_stat = folder_stat = folder_path.stat()
            folder_mtime = folder_stat.st_mtime
            folder_mtime_dt = datetime.fromtimestamp(folder_mtime)
            
            # 计算文件夹中图片的总大小
            total_size = 0
            image_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
            for item in folder_path.iterdir():
                if item.is_file() and item.suffix.lower() in image_extensions:
                    total_size += item.stat().st_size
            
            # 查询数据库中的专辑
            album = db.query(Album).filter(
                Album.file_path == str(folder_path),
                Album.is_active == 1
            ).first()
            
            if album and album.last_scan_time and album.last_scan_time > folder_mtime_dt:
                if total_size == album.file_size:  # 文件大小也相同才跳过
                    return True, "文件夹未修改"
                else:
                    return False, "文件夹内容变化，强制更新"
            
            return False, ""
            
        except Exception as e:
            logger.error(f"检查文件夹跳过状态失败 {folder_path.name}: {e}")
            return False, ""
