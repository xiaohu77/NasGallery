import zipfile
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime
import logging
import io
from PIL import Image

from .archive import ArchiveService, FolderArchiveService

logger = logging.getLogger(__name__)


class CoverService:
    """封面图管理服务 - 使用CBZ文件名直接命名封面
    封面输出为 WebP，尺寸固定为 600x900，并进行裁剪填充（crop to fill）"""
    
    def __init__(self, covers_dir: Path):
        self.covers_dir = covers_dir
        self.covers_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"封面服务初始化: {self.covers_dir}")
    
    def extract_cover_to_folder(self, cbz_path: Path, cover_filename: str, album_id: int) -> Optional[Path]:
        """
        从CBZ提取封面并转换为固定尺寸的 WebP（600x900），保存为 {cbz_stem}.webp
        """
        try:
            # 使用 CBZ stem 作为封面文件名，输出为 WEBP
            cover_name = f"{cbz_path.stem}.webp"
            cover_path = self.covers_dir / cover_name
            
            # 检查是否需要更新（基于 CBZ 文件修改时间）
            if cover_path.exists():
                cbz_mtime = cbz_path.stat().st_mtime
                cover_mtime = cover_path.stat().st_mtime
                if cover_mtime >= cbz_mtime and cover_path.stat().st_size > 1000:
                    logger.debug(f"封面已是最新: {cover_path}")
                    return cover_path
            
            # 从 CBZ 提取封面图片数据
            image_data = ArchiveService.extract_image(cbz_path, cover_filename)
            if not image_data:
                # 尝试使用 CBZ 中的第一张图片作为封面
                image_list = ArchiveService.get_image_list(cbz_path)
                if image_list:
                    logger.warning(f"封面 {cover_filename} 不存在，使用第一张图片 {image_list[0]}")
                    image_data = ArchiveService.extract_image(cbz_path, image_list[0])

            if not image_data:
                logger.error(f"无法从 {cbz_path.name} 提取封面图片")
                return None
            
            # 打开图片并进行裁剪填充到 600x900，输出为 WebP
            img = Image.open(io.BytesIO(image_data))
            target_w, target_h = 600, 900
            orig_w, orig_h = img.size
            scale = max(target_w / orig_w, target_h / orig_h)
            new_w = int(orig_w * scale)
            new_h = int(orig_h * scale)
            img = img.resize((new_w, new_h), Image.LANCZOS)
            left = (new_w - target_w) // 2
            top = (new_h - target_h) // 2
            img = img.crop((left, top, left + target_w, top + target_h))

            # 保存为 WebP
            img.save(cover_path, format='WEBP', quality=85)
            logger.info(f"✅ 封面已生成: {cover_path} ({cover_path.stat().st_size} bytes)")
            return cover_path
            
        except Exception as e:
            logger.error(f"提取封面失败 {cbz_path.name}: {e}")
            return None
    
    def extract_cover_from_folder(self, folder_path: Path, cover_filename: str, album_id: int) -> Optional[Path]:
        """
        从文件夹图集提取封面并转换为固定尺寸的 WebP（600x900），保存为 {folder_name}.webp
        """
        try:
            # 使用文件夹名作为封面文件名，输出为 WEBP
            cover_name = f"{folder_path.name}.webp"
            cover_path = self.covers_dir / cover_name
            
            # 检查是否需要更新（基于文件夹修改时间）
            if cover_path.exists():
                folder_mtime = folder_path.stat().st_mtime
                cover_mtime = cover_path.stat().st_mtime
                if cover_mtime >= folder_mtime and cover_path.stat().st_size > 1000:
                    logger.debug(f"封面已是最新: {cover_path}")
                    return cover_path
            
            # 从文件夹提取封面图片数据
            image_data = FolderArchiveService.extract_image(folder_path, cover_filename)
            if not image_data:
                # 尝试使用文件夹中的第一张图片作为封面
                image_list = FolderArchiveService.get_image_list(folder_path)
                if image_list:
                    logger.warning(f"封面 {cover_filename} 不存在，使用第一张图片 {image_list[0]}")
                    image_data = FolderArchiveService.extract_image(folder_path, image_list[0])

            if not image_data:
                logger.error(f"无法从 {folder_path.name} 提取封面图片")
                return None
            
            # 打开图片并进行裁剪填充到 600x900，输出为 WebP
            img = Image.open(io.BytesIO(image_data))
            target_w, target_h = 600, 900
            orig_w, orig_h = img.size
            scale = max(target_w / orig_w, target_h / orig_h)
            new_w = int(orig_w * scale)
            new_h = int(orig_h * scale)
            img = img.resize((new_w, new_h), Image.LANCZOS)
            left = (new_w - target_w) // 2
            top = (new_h - target_h) // 2
            img = img.crop((left, top, left + target_w, top + target_h))

            # 保存为 WebP
            img.save(cover_path, format='WEBP', quality=85)
            logger.info(f"✅ 封面已生成: {cover_path} ({cover_path.stat().st_size} bytes)")
            return cover_path
            
        except Exception as e:
            logger.error(f"提取封面失败 {folder_path.name}: {e}")
            return None
    
    def get_cover_url(self, cbz_path: Path) -> str:
        """获取封面URL（基于CBZ文件名，WebP 格式）"""
        cover_name = f"{cbz_path.stem}.webp"
        return f"/covers/{cover_name}"
    
    def get_cover_path_by_cbz(self, cbz_path: Path) -> Path:
        """获取封面文件路径（基于CBZ文件名）"""
        cover_name = f"{cbz_path.stem}.webp"
        return self.covers_dir / cover_name
    
    def get_cover_path_by_album_id(self, album_id: int, db) -> Optional[Path]:
        """根据album_id获取封面路径（需要查询数据库）"""
        from ..models import Album
        album = db.query(Album).filter(Album.id == album_id).first()
        if album and album.file_path:
            cbz_path = Path(album.file_path)
            return self.get_cover_path_by_cbz(cbz_path)
        return None
    
    def cover_exists_by_cbz(self, cbz_path: Path) -> bool:
        """检查封面是否存在（基于CBZ文件名）"""
        return self.get_cover_path_by_cbz(cbz_path).exists()
    
    def get_or_create_cover(self, album_path: Path, cover_filename: str = "cover.jpg", album_id: int = None) -> Optional[Path]:
        """
        获取或创建封面（自动判断是CBZ还是文件夹）
        
        Args:
            album_path: 图集路径（CBZ文件或文件夹）
            cover_filename: 封面文件名（默认 cover.jpg）
            album_id: 图集ID（用于日志）
            
        Returns:
            封面路径，失败返回 None
        """
        if album_path.is_file():
            return self.extract_cover_to_folder(album_path, cover_filename, album_id)
        else:
            return self.extract_cover_from_folder(album_path, cover_filename, album_id)
    
    def cleanup_orphaned_covers(self, valid_album_paths: set):
        """
        清理已删除图集的封面（支持CBZ和文件夹图集）
        
        Args:
            valid_album_paths: 有效的图集路径集合（CBZ文件路径或文件夹路径）
        """
        cleaned = 0
        valid_cover_names = set()
        
        for p in valid_album_paths:
            path = Path(p)
            if path.is_file():
                # CBZ文件：使用 stem（去掉扩展名）
                valid_cover_names.add(f"{path.stem}.webp")
            else:
                # 文件夹：使用文件夹名
                valid_cover_names.add(f"{path.name}.webp")
        
        for cover_file in self.covers_dir.glob("*.webp"):
            if cover_file.name not in valid_cover_names:
                try:
                    cover_file.unlink()
                    cleaned += 1
                    logger.info(f"清理已删除图集封面: {cover_file.name}")
                except Exception as e:
                    logger.error(f"清理封面失败 {cover_file.name}: {e}")
        
        if cleaned > 0:
            logger.info(f"✅ 清理完成，删除 {cleaned} 个过期封面")
    
    def get_stats(self) -> dict:
        """获取封面统计信息"""
        cover_files = list(self.covers_dir.glob("*.webp"))
        total_size = sum(f.stat().st_size for f in cover_files)
        
        return {
            "total_covers": len(cover_files),
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "cover_dir": str(self.covers_dir),
            "covers": [f.name for f in cover_files[:10]]  # 显示前10个
        }
