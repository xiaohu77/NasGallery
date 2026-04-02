import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
import re

from ...models import Album, Tag, Organization, Model, AlbumTag

logger = logging.getLogger(__name__)


def sanitize_filename(name: str) -> str:
    """
    规范化文件名，移除或替换特殊字符
    
    Args:
        name: 原始文件名
    
    Returns:
        规范化后的文件名
    """
    # 替换常见的特殊字符
    replacements = {
        '/': '_',
        '\\': '_',
        ':': '_',
        '*': '_',
        '?': '_',
        '"': '_',
        '<': '_',
        '>': '_',
        '|': '_',
        '\n': '_',
        '\r': '_',
        '\t': '_',
    }
    
    result = name
    for old, new in replacements.items():
        result = result.replace(old, new)
    
    # 移除连续的下划线
    result = re.sub(r'_+', '_', result)
    
    # 移除首尾的空格和下划线
    result = result.strip(' _')
    
    return result


class DatabaseUpdater:
    """数据库更新和标签管理器"""
    
    def __init__(self, db: Session, scan_logger):
        """
        初始化数据库更新器
        
        Args:
            db: 数据库会话
            scan_logger: 扫描日志管理器
        """
        self.db = db
        self.scan_logger = scan_logger
    
    def get_or_create_tag(self, name: str, type: str, description: Optional[str] = None) -> Tag:
        """获取或创建标签"""
        try:
            tag = self.db.query(Tag).filter(Tag.name == name, Tag.type == type).first()
            if not tag:
                tag = Tag(
                    name=name,
                    type=type,
                    description=description or name
                )
                self.db.add(tag)
                self.db.flush()
                logger.debug(f"创建标签: {name} ({type})")
            return tag
        except Exception as e:
            logger.error(f"创建标签失败 {name}: {e}")
            raise
    
    def get_or_create_organization(self, name: str, tag: Tag) -> Organization:
        """获取或创建套图"""
        try:
            org = self.db.query(Organization).filter(Organization.name == name).first()
            if not org:
                org = Organization(
                    name=name,
                    description=f'{name}官方写真',
                    tag_id=tag.id
                )
                self.db.add(org)
                self.db.flush()
                logger.debug(f"创建套图: {name}")
            return org
        except Exception as e:
            logger.error(f"创建套图失败 {name}: {e}")
            raise
    
    def get_or_create_model(self, name: str, tag: Tag) -> Model:
        """获取或创建模特"""
        try:
            model = self.db.query(Model).filter(Model.name == name).first()
            if not model:
                model = Model(
                    name=name,
                    description=f'{name}个人写真',
                    tag_id=tag.id
                )
                self.db.add(model)
                self.db.flush()
                logger.debug(f"创建模特: {name}")
            return model
        except Exception as e:
            logger.error(f"创建模特失败 {name}: {e}")
            raise
    
    def update_album_tags(self, album: Album, tag_info: Dict):
        """智能更新图集标签关联"""
        try:
            # 获取当前标签关联
            existing_tags = {t.id: t for t in album.tags}
            
            # 创建新标签列表
            new_tags = []
            
            # 处理套图
            for org_name in tag_info.get('org', []):
                org_tag = self.get_or_create_tag(org_name, 'org', f'{org_name}套图')
                org = self.get_or_create_organization(org_name, org_tag)
                new_tags.append(org_tag)
            
            # 处理模特
            for model_name in tag_info.get('model', []):
                model_tag = self.get_or_create_tag(model_name, 'model', f'{model_name}模特')
                model = self.get_or_create_model(model_name, model_tag)
                new_tags.append(model_tag)
            
            # 处理 Cosplayer
            for cosplayer_name in tag_info.get('cosplayer', []):
                cosplayer_tag = self.get_or_create_tag(cosplayer_name, 'cosplayer', f'{cosplayer_name} Cosplayer')
                new_tags.append(cosplayer_tag)
            
            # 处理 Character
            for character_name in tag_info.get('character', []):
                character_tag = self.get_or_create_tag(character_name, 'character', f'{character_name} 角色')
                new_tags.append(character_tag)
            
            # 处理通用标签
            for tag_name in tag_info.get('tags', []):
                tag = self.get_or_create_tag(tag_name, 'tag', tag_name)
                new_tags.append(tag)
            
            # 智能更新关联
            new_tag_ids = {t.id for t in new_tags}
            existing_tag_ids = set(existing_tags.keys())
            
            # 删除不存在的关联（先减计数）
            to_remove = existing_tag_ids - new_tag_ids
            if to_remove:
                # 先减少被移除标签的计数
                for tag_id in to_remove:
                    tag = existing_tags.get(tag_id)
                    if tag and tag.album_count > 0:
                        tag.album_count -= 1
                
                self.db.query(AlbumTag).filter(
                    AlbumTag.album_id == album.id,
                    AlbumTag.tag_id.in_(to_remove)
                ).delete(synchronize_session=False)
                logger.debug(f"移除标签关联: {album.id} - {len(to_remove)}个")
            
            # 添加新的关联（后加计数）
            to_add = new_tag_ids - existing_tag_ids
            for tag in new_tags:
                if tag.id in to_add:
                    self.db.add(AlbumTag(album_id=album.id, tag_id=tag.id))
                    tag.album_count += 1
            if to_add:
                logger.debug(f"添加标签关联: {album.id} - {len(to_add)}个")
                
        except Exception as e:
            logger.error(f"更新图集标签失败 (Album ID: {album.id}): {e}")
            raise
    
    def create_or_update_album(self, album_path: Path, metadata: Dict, tag_info: Dict, description: Optional[str] = None, album_type: str = 'cbz') -> Album:
        """
        创建或更新专辑
        
        Args:
            album_path: 图集路径（CBZ文件路径或文件夹路径）
            metadata: 元数据（图片列表、封面等）
            tag_info: 标签信息
            description: 专辑描述
            album_type: 图集类型（'cbz' 或 'folder'）
        
        Returns:
            创建或更新的专辑对象
        """
        try:
            # 获取文件信息
            if album_type == 'cbz':
                file_stat = album_path.stat()
                file_size = file_stat.st_size
                file_name = album_path.name
                album_title = sanitize_filename(album_path.stem)  # 规范化标题
            else:
                # 文件夹图集：计算文件夹中所有图片的总大小
                file_size = 0
                image_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
                for item in album_path.iterdir():
                    if item.is_file() and item.suffix.lower() in image_extensions:
                        file_size += item.stat().st_size
                file_name = album_path.name
                album_title = sanitize_filename(album_path.name)  # 规范化标题
            
            # 使用传入的描述或默认标题
            if description:
                album_description = description
            else:
                album_description = None
            
            # 检查是否已存在
            album = self.db.query(Album).filter(
                Album.file_path == str(album_path),
                Album.is_active == 1
            ).first()
            
            is_new = False
            
            if not album:
                # 创建新图集
                album = Album(
                    title=album_title,
                    file_path=str(album_path),
                    file_name=file_name,
                    description=album_description,
                    image_count=metadata['image_count'],
                    cover_image=metadata['cover_image'],
                    file_size=file_size,
                    album_type=album_type,
                    last_scan_time=datetime.utcnow(),
                    is_active=1
                )
                self.db.add(album)
                self.db.flush()
                is_new = True
                self.scan_logger.results['new_albums'] += 1
                self.scan_logger.log_new_file(album_path.name)
            else:
                # 更新现有图集
                album.title = album_title
                album.description = album_description
                album.image_count = metadata['image_count']
                album.cover_image = metadata['cover_image']
                album.file_size = file_size
                album.album_type = album_type
                album.updated_at = datetime.utcnow()
                album.last_scan_time = datetime.utcnow()
                album.is_active = 1  # 恢复已删除的图集
                self.scan_logger.results['updated_albums'] += 1
                self.scan_logger.log_updated_file(album_path.name)
            
            # 智能更新标签关联
            self.update_album_tags(album, tag_info)
            
            return album
            
        except Exception as e:
            logger.error(f"创建或更新专辑失败 {album_path.name}: {e}")
            raise
