import logging
from typing import Dict
from sqlalchemy.orm import Session

from ...models import Album, Tag, Organization, Model, AlbumTag

logger = logging.getLogger(__name__)


class StatsUpdater:
    """统计信息更新器"""
    
    def __init__(self, db: Session):
        """
        初始化统计更新器
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def update_stats_incremental(self, album: Album, tag_info: Dict):
        """
        增量更新统计信息（只更新当前图集涉及的分类）
        用于扫描过程中实时更新统计
        """
        try:
            # 更新涉及的套图统计
            for org_name in tag_info.get('org', []):
                org = self.db.query(Organization).filter(Organization.name == org_name).first()
                if org:
                    count = self.db.query(AlbumTag)\
                        .join(Tag)\
                        .join(Album)\
                        .filter(Tag.id == org.tag_id, Album.is_active == 1)\
                        .count()
                    org.album_count = count
            
            # 更新涉及的模特统计
            for model_name in tag_info.get('model', []):
                model = self.db.query(Model).filter(Model.name == model_name).first()
                if model:
                    count = self.db.query(AlbumTag)\
                        .join(Tag)\
                        .join(Album)\
                        .filter(Tag.id == model.tag_id, Album.is_active == 1)\
                        .count()
                    model.album_count = count
            
            # 更新涉及的 cosplayer 标签统计
            for cosplayer_name in tag_info.get('cosplayer', []):
                tag = self.db.query(Tag).filter(Tag.name == cosplayer_name, Tag.type == 'cosplayer').first()
                if tag:
                    tag.album_count = self.db.query(AlbumTag)\
                        .join(Album)\
                        .filter(AlbumTag.tag_id == tag.id, Album.is_active == 1)\
                        .count()
            
            # 更新涉及的 character 标签统计
            for character_name in tag_info.get('character', []):
                tag = self.db.query(Tag).filter(Tag.name == character_name, Tag.type == 'character').first()
                if tag:
                    tag.album_count = self.db.query(AlbumTag)\
                        .join(Album)\
                        .filter(AlbumTag.tag_id == tag.id, Album.is_active == 1)\
                        .count()
            
            # 更新涉及的标签统计
            for tag_name in tag_info.get('tags', []):
                tag = self.db.query(Tag).filter(Tag.name == tag_name, Tag.type == 'tag').first()
                if tag:
                    tag.album_count = self.db.query(AlbumTag)\
                        .join(Album)\
                        .filter(AlbumTag.tag_id == tag.id, Album.is_active == 1)\
                        .count()
            
            self.db.flush()
            logger.debug(f"增量统计更新完成: {album.title}")
            
        except Exception as e:
            logger.error(f"增量更新统计信息失败: {e}")
            raise
    
    def update_statistics(self):
        """更新所有统计信息（只统计有效图集）"""
        try:
            # 更新套图统计（只统计 is_active=1 的图集）
            for org in self.db.query(Organization).all():
                count = self.db.query(AlbumTag)\
                    .join(Tag)\
                    .join(Album)\
                    .filter(Tag.id == org.tag_id, Album.is_active == 1)\
                    .count()
                org.album_count = count
                if count > 0:
                    album_tag = self.db.query(AlbumTag)\
                        .join(Tag)\
                        .join(Album)\
                        .filter(Tag.id == org.tag_id, Album.is_active == 1)\
                        .first()
                    if album_tag:
                        cover_album = self.db.query(Album).filter(
                            Album.id == album_tag.album_id,
                            Album.is_active == 1
                        ).first()
                        if cover_album and cover_album.cover_image:
                            org.cover_url = f"/api/albums/{cover_album.id}/images/{cover_album.cover_image}"
                else:
                    org.cover_url = None  # 没有有效图集时清空封面
            
            # 更新模特统计（只统计 is_active=1 的图集）
            for model in self.db.query(Model).all():
                count = self.db.query(AlbumTag)\
                    .join(Tag)\
                    .join(Album)\
                    .filter(Tag.id == model.tag_id, Album.is_active == 1)\
                    .count()
                model.album_count = count
                if count > 0:
                    album_tag = self.db.query(AlbumTag)\
                        .join(Tag)\
                        .join(Album)\
                        .filter(Tag.id == model.tag_id, Album.is_active == 1)\
                        .first()
                    if album_tag:
                        cover_album = self.db.query(Album).filter(
                            Album.id == album_tag.album_id,
                            Album.is_active == 1
                        ).first()
                        if cover_album and cover_album.cover_image:
                            model.cover_url = f"/api/albums/{cover_album.id}/images/{cover_album.cover_image}"
                else:
                    model.cover_url = None  # 没有有效图集时清空封面
            
            # 更新标签统计（只统计 is_active=1 的图集）
            for tag in self.db.query(Tag).all():
                tag.album_count = self.db.query(AlbumTag)\
                    .join(Album)\
                    .filter(AlbumTag.tag_id == tag.id, Album.is_active == 1)\
                    .count()
            
        except Exception as e:
            logger.error(f"更新统计信息失败: {e}")
            raise
