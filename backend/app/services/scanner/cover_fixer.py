"""
封面修复服务模块

处理封面修复相关的功能：
- 检测需要修复的图集
- 修复缺失或错误的封面
- 修复错误的 file_path
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime
from sqlalchemy.orm import Session

from ...models import Album

logger = logging.getLogger(__name__)


class CoverFixResult:
    """封面修复结果"""
    
    def __init__(self):
        self.album_ids_needs_fix: List[int] = []
        self.album_fix_reasons: Dict[int, List[str]] = {}
        self.processed = 0
        self.failed = 0
        self.skipped = 0
        self.file_path_fixed = 0
    
    @property
    def count(self) -> int:
        return len(self.album_ids_needs_fix)
    
    def get_reason_summary(self) -> Dict[str, int]:
        """获取修复原因统计"""
        reason_summary = {}
        for reasons in self.album_fix_reasons.values():
            for r in reasons:
                if not r.startswith("找到正确文件"):
                    reason_summary[r] = reason_summary.get(r, 0) + 1
        return reason_summary


class CoverFixer:
    """封面修复服务"""
    
    def __init__(self, db: Session, covers_dir: Path, images_dir: Path):
        """
        初始化封面修复服务
        
        Args:
            db: 数据库会话
            covers_dir: 封面目录
            images_dir: 图片目录
        """
        self.db = db
        self.covers_dir = covers_dir
        self.images_dir = images_dir
    
    def find_correct_file(self, file_name: str) -> Optional[Path]:
        """
        在 images_dir 中查找正确的文件
        
        Args:
            file_name: 文件名（不含路径）
            
        Returns:
            找到的文件路径，未找到返回 None
        """
        if not file_name:
            return None
        
        for item in self.images_dir.rglob(file_name):
            if item.is_file() and item.suffix.lower() in ('.cbz', '.zip'):
                return item
        return None
    
    def _get_correct_cover_name(self, album: Album, need_fix_file_path: bool) -> str:
        """
        获取正确的封面文件名
        
        Args:
            album: 图集对象
            need_fix_file_path: 是否需要修复 file_path
            
        Returns:
            正确的封面文件名
        """
        if need_fix_file_path:
            file_name = album.file_name
            if file_name.endswith(('.cbz', '.zip')):
                return file_name[:-4] + '.webp'
            else:
                return f"{file_name}.webp"
        else:
            album_path = Path(album.file_path)
            if album_path.suffix in ('.cbz', '.zip'):
                return f"{album_path.stem}.webp"
            else:
                return f"{album_path.name}.webp"
    
    def detect_albums_need_fix(self) -> CoverFixResult:
        """
        检测需要修复的图集
        
        Returns:
            检测结果
        """
        result = CoverFixResult()
        all_albums = self.db.query(Album).filter(Album.is_active == 1).all()
        
        for album in all_albums:
            reasons = []
            need_fix_file_path = False
            
            # 1. 检查源文件是否存在
            album_path = Path(album.file_path)
            if not album_path.exists():
                reasons.append("源文件不存在")
                correct_path = self.find_correct_file(album.file_name)
                if correct_path:
                    reasons.append(f"找到正确文件: {correct_path}")
                    need_fix_file_path = True
                else:
                    reasons.append("未找到正确文件")
            
            # 2. 获取正确的封面文件名
            correct_cover_name = self._get_correct_cover_name(album, need_fix_file_path)
            
            # 3. 检查 cover_path
            if not album.cover_path or album.cover_path == '':
                reasons.append("cover_path 为空")
            else:
                cover_name = Path(album.cover_path).name
                cover_file = self.covers_dir / cover_name
                if not cover_file.exists():
                    reasons.append("封面文件不存在")
                if cover_name != correct_cover_name:
                    reasons.append("封面文件名不匹配")
            
            if reasons:
                result.album_fix_reasons[album.id] = reasons
                result.album_ids_needs_fix.append(album.id)
        
        return result
    
    def fix_single_album(self, album_id: int) -> bool:
        """
        修复单个图集的封面
        
        Args:
            album_id: 图集 ID
            
        Returns:
            是否修复成功
        """
        from ...services.cover import CoverService
        
        album = self.db.query(Album).filter(Album.id == album_id).first()
        if not album:
            return False
        
        try:
            album_path = Path(album.file_path)
            
            # 检查并修复 file_path
            if not album_path.exists():
                correct_path = self.find_correct_file(album.file_name)
                if correct_path:
                    old_path = album.file_path
                    album.file_path = str(correct_path)
                    album_path = correct_path
                    logger.info(f"修复 file_path {album_id}: {old_path} -> {correct_path}")
                else:
                    logger.warning(f"跳过 {album_id}: 源文件不存在且未找到替代文件")
                    return False
            
            # 重新生成封面
            cover_service = CoverService(self.covers_dir)
            cover_path = cover_service.get_or_create_cover(album_path)
            
            if cover_path:
                album.cover_path = str(cover_path)
                self.db.commit()
                logger.info(f"修复封面成功 {album_id}: {album_path.name}")
                return True
            else:
                logger.error(f"修复封面失败 {album_id}: 无法生成封面")
                return False
                
        except Exception as e:
            logger.error(f"修复封面失败 {album_id}: {e}")
            self.db.rollback()
            return False
