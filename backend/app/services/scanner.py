import zipfile
import re
import json
import fcntl
import logging
import os
from pathlib import Path
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from ..models import Album, Tag, Organization, Model, AlbumTag
from ..database import SessionLocal
from .cover import CoverService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
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


def extract_metadata_from_cbz(file_path: Path) -> Optional[Dict]:
    """
    从CBZ文件中提取metadata.json数据
    
    Returns:
        metadata dict 或 None (如果读取失败)
    """
    try:
        with zipfile.ZipFile(file_path, 'r') as archive:
            # 查找metadata.json文件
            metadata_files = [f for f in archive.namelist() if f.endswith('metadata.json')]
            if not metadata_files:
                return None
            
            # 读取metadata.json
            metadata_content = archive.read(metadata_files[0]).decode('utf-8')
            metadata = json.loads(metadata_content)
            
            # 验证必要字段
            required_fields = ['institution', 'model', 'title', 'description']
            for field in required_fields:
                if field not in metadata:
                    logger.warning(f"metadata.json缺少字段: {field}")
            
            return metadata
            
    except json.JSONDecodeError as e:
        logger.error(f"metadata.json格式错误: {file_path.name} - {e}")
        return None
    except Exception as e:
        logger.error(f"读取metadata失败: {file_path.name} - {e}")
        return None


def parse_metadata_to_tags(metadata: Dict) -> Dict[str, List[str]]:
    """从metadata解析标签信息"""
    result = {'org': [], 'model': [], 'tags': []}
    
    try:
        # 1. 套图解析
        if 'institution' in metadata:
            institution = metadata['institution']
            org_name = re.sub(r'[A-Za-z]+', '', institution)
            if org_name:
                result['org'].append(org_name)
        
        # 2. 模特解析
        if 'model' in metadata:
            model_name = metadata['model']
            if model_name:
                result['model'].append(model_name)
        
        # 3. 通用标签解析
        title = metadata.get('title', '')
        description = metadata.get('description', '')
        combined_text = title + ' ' + description
        
        keywords = [
            '美腿', '巨乳', '黑丝', '足控', '制服', '高跟', 'cosplay',
            '白丝', 'JK', '教师', '多人', '女仆', '护士', '清纯'
        ]
        
        for keyword in keywords:
            if keyword in combined_text:
                result['tags'].append(keyword)
        
        # 默认标签
        if not result['org'] and not result['model'] and not result['tags']:
            result['tags'].append('默认')
            
    except Exception as e:
        logger.error(f"解析metadata标签失败: {e}")
        result['tags'].append('默认')
    
    return result


def parse_filename(filename: str) -> Dict[str, List[str]]:
    """从文件名解析标签信息（备用方案）"""
    try:
        name = filename.replace('.cbz', '')
        parts = name.split('__')
        
        result = {'org': [], 'model': [], 'tags': []}
        
        # 1. 套图解析
        if len(parts) > 0:
            org_name = re.sub(r'[A-Za-z]+', '', parts[0])
            if org_name:
                result['org'].append(org_name)
        
        # 2. 模特解析（改进版）
        # 模特字段通常在第3个位置（索引2），但需要排除页数格式
        if len(parts) > 2:
            potential_model = parts[2]
            # 检查是否是页数格式（如 75P, 80P, 100P 等）
            if not re.match(r'^\d+P$', potential_model):
                # 检查是否是纯数字（可能是编号）
                if not re.match(r'^\d+$', potential_model):
                    # 检查是否包含日期格式
                    if not re.match(r'^\d{4}\.\d{2}\.\d{2}$', potential_model):
                        result['model'].append(potential_model)
        
        # 3. 通用标签解析
        keywords = [
            '美腿', '巨乳', '黑丝', '足控', '制服', '高跟', 'cosplay',
            '白丝', 'JK', '教师', '多人', '女仆', '护士', '清纯'
        ]
        
        for keyword in keywords:
            if keyword in name:
                result['tags'].append(keyword)
        
        # 默认标签
        if not result['org'] and not result['model'] and not result['tags']:
            result['tags'].append('默认')
            
    except Exception as e:
        logger.error(f"解析文件名失败 {filename}: {e}")
        result = {'org': [], 'model': [], 'tags': ['默认']}
    
    return result


def get_or_create_tag(db: Session, name: str, type: str, description: str = None) -> Tag:
    """获取或创建标签"""
    try:
        tag = db.query(Tag).filter(Tag.name == name, Tag.type == type).first()
        if not tag:
            tag = Tag(
                name=name,
                type=type,
                description=description or name
            )
            db.add(tag)
            db.flush()
            logger.debug(f"创建标签: {name} ({type})")
        return tag
    except Exception as e:
        logger.error(f"创建标签失败 {name}: {e}")
        raise


def get_or_create_organization(db: Session, name: str, tag: Tag) -> Organization:
    """获取或创建套图"""
    try:
        org = db.query(Organization).filter(Organization.name == name).first()
        if not org:
            org = Organization(
                name=name,
                description=f'{name}官方写真',
                tag_id=tag.id
            )
            db.add(org)
            db.flush()
            logger.debug(f"创建套图: {name}")
        return org
    except Exception as e:
        logger.error(f"创建套图失败 {name}: {e}")
        raise


def get_or_create_model(db: Session, name: str, tag: Tag) -> Model:
    """获取或创建模特"""
    try:
        model = db.query(Model).filter(Model.name == name).first()
        if not model:
            model = Model(
                name=name,
                description=f'{name}个人写真',
                tag_id=tag.id
            )
            db.add(model)
            db.flush()
            logger.debug(f"创建模特: {name}")
        return model
    except Exception as e:
        logger.error(f"创建模特失败 {name}: {e}")
        raise


def extract_cbz_metadata(file_path: Path) -> Dict:
    """提取CBZ文件元数据（图片列表和封面）"""
    try:
        with zipfile.ZipFile(file_path, 'r') as archive:
            # 获取图片文件列表
            image_files = [f for f in archive.namelist()
                          if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
            image_files.sort()
            
            # 确定封面
            cover_image = None
            if 'cover.jpg' in image_files:
                cover_image = 'cover.jpg'
            elif image_files:
                cover_image = image_files[0]
            
            return {
                'image_count': len(image_files),
                'cover_image': cover_image,
                'file_list': image_files
            }
    except Exception as e:
        logger.error(f"提取CBZ元数据失败: {e}")
        return {'image_count': 0, 'cover_image': None, 'file_list': []}


def update_album_tags(db: Session, album: Album, tag_info: Dict):
    """智能更新图集标签关联"""
    try:
        # 获取当前标签关联
        existing_tags = {t.id: t for t in album.tags}
        
        # 创建新标签列表
        new_tags = []
        
        # 处理套图
        for org_name in tag_info['org']:
            org_tag = get_or_create_tag(db, org_name, 'org', f'{org_name}套图')
            org = get_or_create_organization(db, org_name, org_tag)
            new_tags.append(org_tag)
        
        # 处理模特
        for model_name in tag_info['model']:
            model_tag = get_or_create_tag(db, model_name, 'model', f'{model_name}模特')
            model = get_or_create_model(db, model_name, model_tag)
            new_tags.append(model_tag)
        
        # 处理通用标签
        for tag_name in tag_info['tags']:
            tag = get_or_create_tag(db, tag_name, 'tag', tag_name)
            new_tags.append(tag)
        
        # 智能更新关联
        new_tag_ids = {t.id for t in new_tags}
        existing_tag_ids = set(existing_tags.keys())
        
        # 删除不存在的关联
        to_remove = existing_tag_ids - new_tag_ids
        if to_remove:
            db.query(AlbumTag).filter(
                AlbumTag.album_id == album.id,
                AlbumTag.tag_id.in_(to_remove)
            ).delete(synchronize_session=False)
            logger.debug(f"移除标签关联: {album.id} - {len(to_remove)}个")
        
        # 添加新的关联
        to_add = new_tag_ids - existing_tag_ids
        for tag_id in to_add:
            db.add(AlbumTag(album_id=album.id, tag_id=tag_id))
        if to_add:
            logger.debug(f"添加标签关联: {album.id} - {len(to_add)}个")
            
    except Exception as e:
        logger.error(f"更新图集标签失败 (Album ID: {album.id}): {e}")
        raise


def update_statistics(db: Session):
    """更新所有统计信息（只统计有效图集）"""
    try:
        # 更新套图统计（只统计 is_active=1 的图集）
        for org in db.query(Organization).all():
            count = db.query(AlbumTag)\
                .join(Tag)\
                .join(Album)\
                .filter(Tag.id == org.tag_id, Album.is_active == 1)\
                .count()
            org.album_count = count
            if count > 0:
                album_tag = db.query(AlbumTag)\
                    .join(Tag)\
                    .join(Album)\
                    .filter(Tag.id == org.tag_id, Album.is_active == 1)\
                    .first()
                if album_tag:
                    cover_album = db.query(Album).filter(
                        Album.id == album_tag.album_id,
                        Album.is_active == 1
                    ).first()
                    if cover_album and cover_album.cover_image:
                        org.cover_url = f"/api/albums/{cover_album.id}/images/{cover_album.cover_image}"
            else:
                org.cover_url = None  # 没有有效图集时清空封面
        
        # 更新模特统计（只统计 is_active=1 的图集）
        for model in db.query(Model).all():
            count = db.query(AlbumTag)\
                .join(Tag)\
                .join(Album)\
                .filter(Tag.id == model.tag_id, Album.is_active == 1)\
                .count()
            model.album_count = count
            if count > 0:
                album_tag = db.query(AlbumTag)\
                    .join(Tag)\
                    .join(Album)\
                    .filter(Tag.id == model.tag_id, Album.is_active == 1)\
                    .first()
                if album_tag:
                    cover_album = db.query(Album).filter(
                        Album.id == album_tag.album_id,
                        Album.is_active == 1
                    ).first()
                    if cover_album and cover_album.cover_image:
                        model.cover_url = f"/api/albums/{cover_album.id}/images/{cover_album.cover_image}"
            else:
                model.cover_url = None  # 没有有效图集时清空封面
        
        # 更新标签统计（只统计 is_active=1 的图集）
        for tag in db.query(Tag).all():
            tag.album_count = db.query(AlbumTag)\
                .join(Album)\
                .filter(AlbumTag.tag_id == tag.id, Album.is_active == 1)\
                .count()
            
    except Exception as e:
        logger.error(f"更新统计信息失败: {e}")
        raise


def detect_deleted_albums(db: Session, existing_files: Set[str], scan_logger: ScanLogger, cache_service=None):
    """检测并标记已删除的图集，同时清理缓存"""
    try:
        # 查找数据库中所有有效图集
        albums = db.query(Album).filter(Album.is_active == 1).all()
        
        deleted_count = 0
        for album in albums:
            if album.file_path not in existing_files:
                # 标记为已删除
                album.is_active = 0
                album.updated_at = datetime.utcnow()
                scan_logger.log_deleted_album(album.id, album.title)
                deleted_count += 1
                
                # 清理对应的缓存文件
                if cache_service:
                    try:
                        # 清理图片列表缓存
                        cache_service.clear_album_image_list(album.id)
                        # 清理提取图片缓存
                        cache_service.clear_album_extracted_images(album.id)
                        # 清理元数据缓存
                        cache_service.clear_album_metadata(album.id)
                        logger.debug(f"已清理图集 {album.id} 的缓存文件")
                    except Exception as e:
                        logger.warning(f"清理图集 {album.id} 缓存失败: {e}")
        
        if deleted_count > 0:
            logger.info(f"检测到 {deleted_count} 个已删除的图集，并清理对应缓存")
            
    except Exception as e:
        logger.error(f"检测删除图集失败: {e}")
        raise


def scan_albums(db: Session, scan_path: Path = None, use_lock: bool = True) -> Dict:
    """
    扫描目录并更新数据库（完整功能版）
    
    Args:
        db: 数据库会话
        scan_path: 扫描路径
        use_lock: 是否使用文件锁防止并发扫描
    
    Returns:
        扫描结果和详细日志
    """
    if scan_path is None:
        from ..config import settings
        scan_path = settings.IMAGES_DIR
    
    # 初始化封面服务
    from ..config import settings
    from .cache import cache_service
    cover_service = CoverService(settings.COVERS_DIR)
    
    scan_logger = ScanLogger()
    
    # 文件锁路径
    lock_file = Path("/tmp/girlatlas_scan.lock")
    
    def acquire_lock():
        if not use_lock:
            return True
        try:
            lock_file.parent.mkdir(parents=True, exist_ok=True)
            lock_fd = open(lock_file, 'w')
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return lock_fd
        except (IOError, BlockingIOError):
            logger.error("扫描正在进行中，请稍后再试")
            return None
    
    def release_lock(lock_fd):
        if lock_fd and use_lock:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
                lock_fd.close()
                if lock_file.exists():
                    lock_file.unlink()
            except:
                pass
    
    # 获取文件锁
    lock_fd = acquire_lock()
    if not lock_fd:
        scan_logger.log_error("全局", "扫描锁获取失败，可能有其他扫描任务正在进行")
        return scan_logger.get_summary()
    
    try:
        logger.info(f"🚀 开始扫描: {scan_path}")
        
        # 1. 查找所有CBZ文件（包括软连接中的内容）
        try:
            cbz_files = []
            
            # 使用 os.walk 并启用跟随软连接
            for root, dirs, files in os.walk(scan_path, followlinks=True):
                for file in files:
                    if file.endswith('.cbz'):
                        file_path = Path(root) / file
                        cbz_files.append(file_path)
            
            existing_files = {str(f) for f in cbz_files}
            logger.info(f"📁 发现 {len(cbz_files)} 个CBZ文件（包括软连接中的内容）")
        except Exception as e:
            scan_logger.log_error("文件扫描", f"无法访问目录: {e}")
            return scan_logger.get_summary()
        
        # 2. 检测已删除的图集并清理缓存
        detect_deleted_albums(db, existing_files, scan_logger, cache_service)
        
        # 3. 处理每个CBZ文件
        for cbz_file in cbz_files:
            try:
                # 检查文件是否存在且可读
                if not cbz_file.exists():
                    scan_logger.log_error(cbz_file.name, "文件不存在")
                    continue
                
                # 获取文件信息
                file_stat = cbz_file.stat()
                file_mtime = file_stat.st_mtime
                file_size = file_stat.st_size
                file_mtime_dt = datetime.fromtimestamp(file_mtime)
                
                scan_logger.results['scanned_files'] += 1
                
                # 检查是否需要跳过（文件未修改）
                album = db.query(Album).filter(
                    Album.file_path == str(cbz_file),
                    Album.is_active == 1
                ).first()
                
                if album and album.last_scan_time and album.last_scan_time > file_mtime_dt:
                    if file_size == album.file_size:  # 文件大小也相同才跳过
                        scan_logger.log_skipped_file(cbz_file.name, "文件未修改")
                        scan_logger.results['skipped_files'] += 1
                        continue
                    else:
                        scan_logger.log_warning(cbz_file.name, "文件大小变化，强制更新")
                
                # 优先从metadata.json提取信息
                metadata_json = extract_metadata_from_cbz(cbz_file)
                
                tag_info = {}
                album_title = cbz_file.stem
                album_description = None
                
                if metadata_json:
                    # 使用metadata.json的数据，但模特字段从文件名获取
                    tag_info = parse_metadata_to_tags(metadata_json)
                    # 重新从文件名解析模特字段
                    filename_tags = parse_filename(cbz_file.name)
                    tag_info['model'] = filename_tags['model']
                    
                    album_title = metadata_json.get('title', cbz_file.stem)
                    album_description = metadata_json.get('description')
                    scan_logger.log_debug(f"使用metadata（模特从文件名获取）: {cbz_file.name}")
                else:
                    # 降级使用文件名解析
                    tag_info = parse_filename(cbz_file.name)
                    scan_logger.log_warning(cbz_file.name, "使用文件名解析（未找到metadata.json）")
                
                # 提取CBZ文件的图片元数据
                cbz_metadata = extract_cbz_metadata(cbz_file)
                
                if cbz_metadata['image_count'] == 0:
                    scan_logger.log_warning(cbz_file.name, "未找到图片文件")
                
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
                    db.add(album)
                    db.flush()
                    is_new = True
                    scan_logger.results['new_albums'] += 1
                    scan_logger.log_new_file(cbz_file.name)
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
                    scan_logger.results['updated_albums'] += 1
                    scan_logger.log_updated_file(cbz_file.name)
                
                # 智能更新标签关联
                update_album_tags(db, album, tag_info)
                
                # 新增：提取封面到专用目录（使用CBZ文件名）
                if cbz_metadata['cover_image']:
                    cover_path = cover_service.extract_cover_to_folder(
                        cbz_file,
                        cbz_metadata['cover_image'],
                        album.id
                    )
                    if cover_path:
                        album.cover_path = str(cover_path)
                        logger.debug(f"封面已更新: {album.id}")
                
            except Exception as e:
                scan_logger.log_error(cbz_file.name, str(e))
                continue
        
        # 4. 提交所有更改
        try:
            db.commit()
            logger.info("✅ 数据库更改已提交")
            
            # 5. 清理已删除图集的封面
            logger.info("🧹 清理孤儿封面...")
            valid_cbz_paths = {album.file_path for album in db.query(Album).filter(Album.is_active == 1).all()}
            cover_service.cleanup_orphaned_covers(valid_cbz_paths)
            
            # 6. 更新统计信息
            logger.info("📊 更新统计信息...")
            update_statistics(db)
            db.commit()
            logger.info("✅ 统计信息已更新")
            
        except Exception as e:
            logger.error(f"数据库提交失败: {e}")
            db.rollback()
            scan_logger.log_error("数据库提交", str(e))
            scan_logger.results['errors'] += 1
        
    except Exception as e:
        logger.error(f"扫描过程异常: {e}")
        scan_logger.log_error("扫描过程", str(e))
        db.rollback()
    
    finally:
        # 释放文件锁
        release_lock(lock_fd)
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