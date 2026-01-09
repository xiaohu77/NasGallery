import zipfile
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime
import logging

from .archive import ArchiveService

logger = logging.getLogger(__name__)


class CoverService:
    """封面图管理服务 - 使用CBZ文件名直接命名封面"""
    
    def __init__(self, covers_dir: Path):
        self.covers_dir = covers_dir
        self.covers_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"封面服务初始化: {self.covers_dir}")
    
    def extract_cover_to_folder(self, cbz_path: Path, cover_filename: str, album_id: int) -> Optional[Path]:
        """
        从CBZ提取封面到 tmp/cover/{cbz_stem}.jpg
        
        Args:
            cbz_path: CBZ文件路径
            cover_filename: 封面在CBZ中的文件名
            album_id: 图集ID
        
        Returns:
            封面文件路径，失败返回None
        """
        try:
            # 使用CBZ文件名作为封面文件名（去掉.cbz扩展名，添加.jpg）
            cover_name = f"{cbz_path.stem}.jpg"
            cover_path = self.covers_dir / cover_name
            
            # 检查是否需要更新（基于CBZ文件修改时间）
            if cover_path.exists():
                cbz_mtime = cbz_path.stat().st_mtime
                cover_mtime = cover_path.stat().st_mtime
                
                # 如果封面比CBZ新，且文件大小合理，跳过
                if cover_mtime >= cbz_mtime and cover_path.stat().st_size > 1000:
                    logger.debug(f"封面已是最新: {cover_path}")
                    return cover_path
            
            # 从CBZ提取封面图片
            image_data = ArchiveService.extract_image(cbz_path, cover_filename)
            
            # 如果指定封面不存在，使用第一张图片
            if not image_data:
                image_list = ArchiveService.get_image_list(cbz_path)
                if image_list:
                    logger.warning(f"封面 {cover_filename} 不存在，使用第一张图片 {image_list[0]}")
                    image_data = ArchiveService.extract_image(cbz_path, image_list[0])
            
            if not image_data:
                logger.error(f"无法从 {cbz_path.name} 提取封面图片")
                return None
            
            # 优化封面尺寸（适合卡片显示，提高清晰度）
            # optimized_data = ArchiveService.resize_image(image_data, width=600, height=800)
            optimized_data = image_data
            # 保存封面
            cover_path.write_bytes(optimized_data)
            
            logger.info(f"✅ 封面已提取: {cover_path} ({len(optimized_data)} bytes)")
            return cover_path
            
        except Exception as e:
            logger.error(f"提取封面失败 {cbz_path.name}: {e}")
            return None
    
    def get_cover_url(self, cbz_path: Path) -> str:
        """获取封面URL（基于CBZ文件名）"""
        cover_name = f"{cbz_path.stem}.jpg"
        return f"/covers/{cover_name}"
    
    def get_cover_path_by_cbz(self, cbz_path: Path) -> Path:
        """获取封面文件路径（基于CBZ文件名）"""
        cover_name = f"{cbz_path.stem}.jpg"
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
    
    def cleanup_orphaned_covers(self, valid_cbz_paths: set):
        """
        清理已删除图集的封面（基于CBZ文件名）
        
        Args:
            valid_cbz_paths: 有效的CBZ文件路径集合
        """
        cleaned = 0
        valid_cover_names = {f"{Path(p).stem}.jpg" for p in valid_cbz_paths}
        
        for cover_file in self.covers_dir.glob("*.jpg"):
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
        cover_files = list(self.covers_dir.glob("*.jpg"))
        total_size = sum(f.stat().st_size for f in cover_files)
        
        return {
            "total_covers": len(cover_files),
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "cover_dir": str(self.covers_dir),
            "covers": [f.name for f in cover_files[:10]]  # 显示前10个
        }