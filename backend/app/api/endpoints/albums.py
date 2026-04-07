from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from pathlib import Path
from datetime import datetime, timedelta

from app.database import get_db
from app.models import Album, AlbumTag, Tag, User, Organization, Model
from app.schemas import AlbumSummary, AlbumResponse, PagedResponse
from app.services.archive import ArchiveService, FolderArchiveService
from app.services.cover import CoverService
from app.services.cache import cache_service
from app.config import settings
from app.api.deps import DependsDB
from app.api.endpoints.auth import get_current_user
from app.utils import get_cover_url, paginate

router = APIRouter(prefix="/api/albums", tags=["albums"])


def _build_album_summary(album: Album) -> AlbumSummary:
    """构建图集摘要对象"""
    return AlbumSummary(
        id=album.id,
        title=album.title,
        cover_url=get_cover_url(album),
        image_count=album.image_count or 0,
        tags=[t.name for t in album.tags],
        description=album.description,
        view_count=album.view_count or 0
    )


def _get_albums_by_tag_id(
    db: Session,
    tag_id: int,
    tag_type: Optional[str] = None,
    error_not_found: str = "标签不存在",
    page: int = 1,
    size: int = 20
) -> PagedResponse:
    """通用的按标签ID获取图集函数"""
    # 验证标签是否存在
    tag_query = db.query(Tag).filter(Tag.id == tag_id)
    if tag_type:
        tag_query = tag_query.filter(Tag.type == tag_type)
    tag = tag_query.first()
    
    if not tag:
        raise HTTPException(status_code=404, detail=error_not_found)
    
    # 通过标签筛选图集
    query = db.query(Album).join(AlbumTag).filter(
        AlbumTag.tag_id == tag_id,
        Album.is_active == 1
    ).order_by(Album.created_at.desc())
    
    # 分页
    total, albums = paginate(query, page, size)
    
    # 构建响应
    items = [_build_album_summary(album) for album in albums]
    
    return PagedResponse(
        total=total,
        page=page,
        size=size,
        items=items
    )


@router.get("/", response_model=PagedResponse)
async def get_albums(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    tag_type: Optional[str] = Query(None),
    sort: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    获取图集列表（分页）
    
    - page: 页码
    - size: 每页数量（最大100）
    - search: 搜索关键词（匹配标题和描述）
    - tag_type: 按标签类型筛选
    - sort: 排序方式 - recent(近期新增), popular(浏览最多), favorites(用户收藏), history(历史浏览)
    """
    query = db.query(Album).filter(Album.is_active == 1)
    
    # 搜索过滤
    if search:
        query = query.filter(
            or_(
                Album.title.contains(search),
                Album.description.contains(search)
            )
        )
    
    # 标签类型过滤
    if tag_type:
        query = query.join(Album.tags).filter(Tag.type == tag_type)
    
    # 排序方式
    if sort == 'popular':
        # 浏览最多 - 按浏览量降序
        query = query.order_by(Album.view_count.desc().nullslast(), Album.created_at.desc())
    elif sort == 'recent':
        # 近期新增 - 按更新时间降序（近一周内更新的）
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        query = query.filter(Album.updated_at >= one_week_ago).order_by(Album.updated_at.desc())
    else:
        # 默认按创建时间降序
        query = query.order_by(Album.created_at.desc())
    
    # 分页查询（使用子查询加载标签，避免N+1问题）
    from sqlalchemy.orm import joinedload
    query = query.options(joinedload(Album.tags))
    
    total, albums = paginate(query, page, size)
    
    # 构建响应
    items = [_build_album_summary(album) for album in albums]
    
    return PagedResponse(
        total=total,
        page=page,
        size=size,
        items=items
    )


@router.get("/org/{org_id}", response_model=PagedResponse)
async def get_albums_by_organization(
    org_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """根据组织（套图）筛选图集列表"""
    # 验证组织是否存在
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="组织不存在")
    
    return _get_albums_by_tag_id(
        db=db,
        tag_id=org.tag_id,
        error_not_found="组织不存在",
        page=page,
        size=size
    )


@router.get("/model/{model_id}", response_model=PagedResponse)
async def get_albums_by_model(
    model_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """根据模特筛选图集列表"""
    # 验证模特是否存在
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="模特不存在")
    
    return _get_albums_by_tag_id(
        db=db,
        tag_id=model.tag_id,
        error_not_found="模特不存在",
        page=page,
        size=size
    )


@router.get("/cosplayer/{tag_id}", response_model=PagedResponse)
async def get_albums_by_cosplayer(
    tag_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """根据 Cosplayer 筛选图集列表"""
    return _get_albums_by_tag_id(
        db=db,
        tag_id=tag_id,
        tag_type='cosplayer',
        error_not_found="Cosplayer 不存在",
        page=page,
        size=size
    )


@router.get("/character/{tag_id}", response_model=PagedResponse)
async def get_albums_by_character(
    tag_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """根据角色筛选图集列表"""
    return _get_albums_by_tag_id(
        db=db,
        tag_id=tag_id,
        tag_type='character',
        error_not_found="角色不存在",
        page=page,
        size=size
    )


@router.get("/tag/{tag_id}", response_model=PagedResponse)
async def get_albums_by_tag(
    tag_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """根据标签筛选图集列表"""
    return _get_albums_by_tag_id(
        db=db,
        tag_id=tag_id,
        error_not_found="标签不存在",
        page=page,
        size=size
    )

@router.get("/{album_id}", response_model=AlbumResponse)
async def get_album(album_id: int, db: Session = Depends(get_db)):
    """
    获取图集详情
    """
    album = db.query(Album).filter(
        Album.id == album_id,
        Album.is_active == 1
    ).first()
    if not album:
        raise HTTPException(status_code=404, detail="图集不存在")
    
    return album

@router.get("/{album_id}/images")
async def get_album_images(
    album_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    获取图集图片列表（支持分页）
    优先级: 内存缓存 > 文件缓存 > 数据库 > CBZ文件处理
    """
    # 1. 优先从内存缓存读取图片列表
    cached_images = cache_service.get_image_list(album_id)
    if not cached_images:
        # 2. 其次从文件缓存读取图片列表
        cached_images = cache_service.get_image_list_from_file(album_id)
        if cached_images:
            # 同时缓存到内存
            cache_service.set_image_list(album_id, cached_images)
    
    if not cached_images:
        # 3. 缓存未命中，验证图集存在性并处理图集文件
        album = db.query(Album).filter(
            Album.id == album_id,
            Album.is_active == 1
        ).first()
        if not album:
            raise HTTPException(status_code=404, detail="图集不存在")
        
        album_path = Path(album.file_path)
        if not album_path.exists():
            raise HTTPException(status_code=404, detail="图集文件不存在")
        
        # 根据图集类型选择不同的处理方式
        if album.album_type == 'folder':
            print(f"🔄 [图片列表] 从文件夹处理: {album_path.name}")
            image_list = FolderArchiveService.process_and_cache_folder(album_path, album_id)
        else:
            print(f"🔄 [图片列表] 从CBZ文件处理: {album_path.name}")
            image_list = ArchiveService.process_and_cache_cbz(album_path, album_id)
        
        cached_images = image_list
    
    # 分页处理
    total = len(cached_images)
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    
    # 获取分页数据
    paginated_images = cached_images[start_idx:end_idx] if start_idx < total else []
    
    # 构建图片URL
    images = [{"name": filename, "url": f"/albums/{album_id}/images/{filename}"} for filename in paginated_images]
    
    return {
        "album_id": album_id,
        "total": total,
        "page": page,
        "size": size,
        "has_more": end_idx < total,
        "images": images
    }

@router.get("/{album_id}/images/{filename}")
async def get_image_content(
    album_id: int,
    filename: str,
    width: Optional[int] = None,
    height: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    获取图片内容（支持缩放）
    优先级: 文件缓存 > 数据库 > CBZ文件处理
    """
    # 1. 优先从文件缓存读取
    cache_dir = cache_service.extracted_images_dir / str(album_id)
    cache_file = cache_dir / filename
    if cache_file.exists():
        try:
            with open(cache_file, 'rb') as f:
                image_data = f.read()
            print(f"✅ [图片提取] 文件缓存命中: {filename}")
            
            # 缩放处理
            if width or height:
                image_data = ArchiveService.resize_image(image_data, width, height)
                # 缩放后固定返回 JPEG
                media_type = 'image/jpeg'
            else:
                # 根据文件扩展名确定媒体类型
                ext = filename.lower().split('.')[-1]
                media_type_map = {
                    'jpg': 'image/jpeg',
                    'jpeg': 'image/jpeg',
                    'png': 'image/png',
                    'webp': 'image/webp'
                }
                media_type = media_type_map.get(ext, 'image/jpeg')
            
            from fastapi.responses import Response
            return Response(
                content=image_data,
                media_type=media_type,
                headers={
                    "Cache-Control": "public, max-age=31536000",  # 1年缓存
                    "ETag": f'"{cache_file.stat().st_mtime}"'
                }
            )
        except Exception as e:
            print(f"❌ [文件缓存] 读取失败: {e}")
    
    # 2. 请求数据库，处理图集文件
    print(f"🔄 [图片提取] 从图集文件处理: {filename}")
    
    # 调用统一的处理函数（会缓存所有图片）
    album = db.query(Album).filter(
        Album.id == album_id,
        Album.is_active == 1
    ).first()
    if not album:
        raise HTTPException(status_code=404, detail="图集不存在")
    
    album_path = Path(album.file_path)
    if not album_path.exists():
        raise HTTPException(status_code=404, detail="图集文件不存在")
    
    # 根据图集类型选择不同的处理方式
    if album.album_type == 'folder':
        print(f"🔄 [图片提取] 从文件夹处理: {album_path.name}")
        image_list = FolderArchiveService.process_and_cache_folder(album_path, album_id)
    else:
        print(f"🔄 [图片提取] 从CBZ文件处理: {album_path.name}")
        image_list = ArchiveService.process_and_cache_cbz(album_path, album_id)
    
    # 从缓存中获取指定图片
    image_data = cache_service.get_extracted_image(album_id, filename)
    if not image_data:
        raise HTTPException(status_code=404, detail="图片不存在")
    
    # 缩放处理
    if width or height:
        image_data = ArchiveService.resize_image(image_data, width, height)
        # 缩放后固定返回 JPEG
        media_type = 'image/jpeg'
    else:
        # 根据文件扩展名确定媒体类型
        ext = filename.lower().split('.')[-1]
        media_type_map = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'webp': 'image/webp'
        }
        media_type = media_type_map.get(ext, 'image/jpeg')
    
    from fastapi.responses import Response
    return Response(
        content=image_data,
        media_type=media_type,
        headers={
            "Cache-Control": "public, max-age=31536000",  # 1年缓存
            "ETag": f'"{filename}"'
        }
    )

@router.post("/{album_id}/refresh")
async def refresh_album(
    album_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    刷新指定图集的元数据
    """
    from ...services.scanner import extract_cbz_metadata
    
    album = db.query(Album).filter(
        Album.id == album_id,
        Album.is_active == 1
    ).first()
    if not album:
        raise HTTPException(status_code=404, detail="图集不存在")
    
    cbz_path = Path(album.file_path)
    if not cbz_path.exists():
        raise HTTPException(status_code=404, detail="CBZ文件不存在")
    
    # 重新提取元数据
    metadata = extract_cbz_metadata(cbz_path)
    album.image_count = metadata['image_count']
    album.cover_image = metadata['cover_image']
    album.updated_at = datetime.utcnow()
    
    db.commit()
    
    # 清除相关缓存
    cache_service.clear_cache("lists")
    
    return {
        "success": True,
        "message": "图集已刷新",
        "album_id": album_id,
        "image_count": metadata['image_count']
    }


# ==================== 缓存管理API ====================

@router.get("/cache/stats")
async def get_cache_stats(current_user: User = Depends(get_current_user)):
    """
    获取缓存统计信息
    """
    return cache_service.get_cache_stats()


@router.post("/cache/clear")
async def clear_cache(
    cache_type: str = "all",
    current_user: User = Depends(get_current_user)
):
    """
    清除缓存
    
    Args:
        cache_type: 缓存类型 - all/lists/images/metadata
    """
    if cache_type not in ["all", "lists", "images", "metadata"]:
        raise HTTPException(status_code=400, detail="无效的缓存类型")
    
    cleared_count = cache_service.clear_cache(cache_type)
    
    return {
        "success": True,
        "message": f"清除了 {cleared_count} 个缓存项",
        "cache_type": cache_type,
        "cleared_count": cleared_count
    }


@router.post("/cache/cleanup")
async def cleanup_expired_cache(current_user: User = Depends(get_current_user)):
    """
    手动触发过期缓存清理
    """
    cache_service.cleanup_expired()
    return {
        "success": True,
        "message": "过期缓存清理完成"
    }
