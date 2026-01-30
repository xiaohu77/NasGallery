import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from ...models import Album, Tag, Organization, Model, AlbumTag

logger = logging.getLogger(__name__)


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
            for org_name in tag_info['org']:
                org_tag = self.get_or_create_tag(org_name, 'org', f'{org_name}套图')
                org = self.get_or_create_organization(org_name, org_tag)
                new_tags.append(org_tag)
            
            # 处理模特
            for model_name in tag_info['model']:
                model_tag = self.get_or_create_tag(model_name, 'model', f'{model_name}模特')
                model = self.get_or_create_model(model_name, model_tag)
                new_tags.append(model_tag)
            
            # 处理通用标签
            for tag_name in tag_info['tags']:
                tag = self.get_or_create_tag(tag_name, 'tag', tag_name)
                new_tags.append(tag)
            
            # 智能更新关联
            new_tag_ids = {t.id for t in new_tags}
            existing_tag_ids = set(existing_tags.keys())
            
            # 删除不存在的关联
            to_remove = existing_tag_ids - new_tag_ids
            if to_remove:
                self.db.query(AlbumTag).filter(
                    AlbumTag.album_id == album.id,
                    AlbumTag.tag_id.in_(to_remove)
                ).delete(synchronize_session=False)
                logger.debug(f"移除标签关联: {album.id} - {len(to_remove)}个")
            
            # 添加新的关联
            to_add = new_tag_ids - existing_tag_ids
            for tag_id in to_add:
                self.db.add(AlbumTag(album_id=album.id, tag_id=tag_id))
            if to_add:
                logger.debug(f"添加标签关联: {album.id} - {len(to_add)}个")
                
        except Exception as e:
            logger.error(f"更新图集标签失败 (Album ID: {album.id}): {e}")
            raise
    
    def create_or_update_album(self, cbz_file: Path, cbz_metadata: Dict, tag_info: Dict, description: Optional[str] = None) -> Album:
        """
        创建或更新专辑
        
        Args:
            cbz_file: CBZ文件路径
            cbz_metadata: CBZ元数据（图片列表、封面等）
            tag_info: 标签信息
            description: 专辑描述
        
        Returns:
            创建或更新的专辑对象
        """
        try:
            # 获取文件信息
            file_stat = cbz_file.stat()
            file_size = file_stat.st_size
            
            # 从metadata或文件名获取标题和描述
            album_title = cbz_file.stem
            album_description = description
            
            # 检查是否已存在
            album = self.db.query(Album).filter(
                Album.file_path == str(cbz_file),
                Album.is_active == 1
            ).first()
            
            is_new = False
            
            if not album:
                # 创建新图集
                album = Album(
                    title=album_title,
                    file_path=str(cbz_file),
                    file_name=cbz_file.name,
                    description=album_description,
                    image_count=cbz_metadata['image_count'],
                    cover_image=cbz_metadata['cover_image'],
                    file_size=file_size,
                    last_scan_time=datetime.utcnow(),
                    is_active=1
                )
                self.db.add(album)
                self.db.flush()
                is_new = True
                self.scan_logger.results['new_albums'] += 1
                self.scan_logger.log_new_file(cbz_file.name)
            else:
                # 更新现有图集
                album.title = album_title
                album.description = album_description
                album.image_count = cbz_metadata['image_count']
                album.cover_image = cbz_metadata['cover_image']
                album.file_size = file_size
                album.updated_at = datetime.utcnow()
                album.last_scan_time = datetime.utcnow()
                album.is_active = 1  # 恢复已删除的图集
                self.scan_logger.results['updated_albums'] += 1
                self.scan_logger.log_updated_file(cbz_file.name)
            
            # 智能更新标签关联
            self.update_album_tags(album, tag_info)
            
            return album
            
        except Exception as e:
            logger.error(f"创建或更新专辑失败 {cbz_file.name}: {e}")
            raise
