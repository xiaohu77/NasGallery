from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pathlib import Path
from datetime import datetime

from ...database import get_db
from ...models import Album, AlbumTag, Tag
from ...schemas import AlbumSummary, AlbumResponse, PagedResponse
from ...services.archive import ArchiveService
from ...services.cover import CoverService
from ...services.cache import cache_service
from ...config import settings

router = APIRouter(prefix="/albums", tags=["albums"])

@router.get("/", response_model=PagedResponse)
async def get_albums(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    tag_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取图集列表，支持分页、标签筛选和搜索
    """
    query = db.query(Album)
    
    # 标签筛选
    if tag_id:
        query = query.join(AlbumTag).filter(AlbumTag.tag_id == tag_id)
    
    # 搜索
    if search:
        query = query.filter(Album.title.contains(search))
    
    # 总数
    total = query.count()
    
    # 分页查询
    albums = query.order_by(Album.created_at.desc())\
                 .offset((page - 1) * size)\
                 .limit(size)\
                 .all()
    
    # 构建响应
    items = []
    for album in albums:
        cover_url = None
        
        # 优先使用预提取的封面路径
        if album.cover_path:
            # 使用静态文件URL（基于CBZ文件名）
            cover_url = f"/covers/{Path(album.file_path).stem}.jpg"
        elif album.cover_image:
            # 降级：使用API接口（兼容旧数据）
            cover_url = f"/albums/{album.id}/images/{album.cover_image}"
        
        items.append(AlbumSummary(
            id=album.id,
            title=album.title,
            cover_url=cover_url,
            image_count=album.image_count or 0,
            tags=[t.name for t in album.tags],
            description=album.description
        ))
    
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
    """
    根据组织（套图）筛选图集列表
    """
    from ...models import Organization
    
    # 验证组织是否存在
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="组织不存在")
    
    # 通过组织关联的标签来筛选图集
    query = db.query(Album).join(AlbumTag).filter(AlbumTag.tag_id == org.tag_id)
    
    # 总数
    total = query.count()
    
    # 分页查询
    albums = query.order_by(Album.created_at.desc())\
                 .offset((page - 1) * size)\
                 .limit(size)\
                 .all()
    
    # 构建响应
    items = []
    for album in albums:
        cover_url = None
        
        if album.cover_path:
            cover_url = f"/covers/{Path(album.file_path).stem}.jpg"
        elif album.cover_image:
            cover_url = f"/albums/{album.id}/images/{album.cover_image}"
        
        items.append(AlbumSummary(
            id=album.id,
            title=album.title,
            cover_url=cover_url,
            image_count=album.image_count or 0,
            tags=[t.name for t in album.tags],
            description=album.description
        ))
    
    return PagedResponse(
        total=total,
        page=page,
        size=size,
        items=items
    )


@router.get("/model/{model_id}", response_model=PagedResponse)
async def get_albums_by_model(
    model_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    根据模特筛选图集列表
    """
    from ...models import Model
    
    # 验证模特是否存在
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="模特不存在")
    
    # 通过模特关联的标签来筛选图集
    query = db.query(Album).join(AlbumTag).filter(AlbumTag.tag_id == model.tag_id)
    
    # 总数
    total = query.count()
    
    # 分页查询
    albums = query.order_by(Album.created_at.desc())\
                 .offset((page - 1) * size)\
                 .limit(size)\
                 .all()
    
    # 构建响应
    items = []
    for album in albums:
        cover_url = None
        
        if album.cover_path:
            cover_url = f"/covers/{Path(album.file_path).stem}.jpg"
        elif album.cover_image:
            cover_url = f"/albums/{album.id}/images/{album.cover_image}"
        
        items.append(AlbumSummary(
            id=album.id,
            title=album.title,
            cover_url=cover_url,
            image_count=album.image_count or 0,
            tags=[t.name for t in album.tags],
            description=album.description
        ))
    
    return PagedResponse(
        total=total,
        page=page,
        size=size,
        items=items
    )


@router.get("/tag/{tag_id}", response_model=PagedResponse)
async def get_albums_by_tag(
    tag_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    根据标签筛选图集列表
    """
    from ...models import Tag
    
    # 验证标签是否存在
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    
    # 通过标签筛选图集
    query = db.query(Album).join(AlbumTag).filter(AlbumTag.tag_id == tag_id)
    
    # 总数
    total = query.count()
    
    # 分页查询
    albums = query.order_by(Album.created_at.desc())\
                 .offset((page - 1) * size)\
                 .limit(size)\
                 .all()
    
    # 构建响应
    items = []
    for album in albums:
        cover_url = None
        
        if album.cover_path:
            cover_url = f"/covers/{Path(album.file_path).stem}.jpg"
        elif album.cover_image:
            cover_url = f"/albums/{album.id}/images/{album.cover_image}"
        
        items.append(AlbumSummary(
            id=album.id,
            title=album.title,
            cover_url=cover_url,
            image_count=album.image_count or 0,
            tags=[t.name for t in album.tags],
            description=album.description
        ))
    
    return PagedResponse(
        total=total,
        page=page,
        size=size,
        items=items
    )

@router.get("/{album_id}", response_model=AlbumResponse)
async def get_album(album_id: int, db: Session = Depends(get_db)):
    """
    获取图集详情
    """
    album = db.query(Album).filter(Album.id == album_id).first()
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
        # 3. 缓存未命中，验证图集存在性并处理CBZ文件
        album = db.query(Album).filter(Album.id == album_id).first()
        if not album:
            raise HTTPException(status_code=404, detail="图集不存在")
        
        cbz_path = Path(album.file_path)
        if not cbz_path.exists():
            raise HTTPException(status_code=404, detail="CBZ文件不存在")
        
        print(f"🔄 [图片列表] 从CBZ文件处理: {cbz_path.name}")
        
        # 直接解压并缓存全部图片信息
        image_list = ArchiveService.process_and_cache_cbz(cbz_path, album_id)
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
            
            from fastapi.responses import Response
            return Response(content=image_data, media_type="image/jpeg")
        except Exception as e:
            print(f"❌ [文件缓存] 读取失败: {e}")
    
    # 2. 请求数据库，处理CBZ文件
    print(f"🔄 [图片提取] 从CBZ文件处理: {filename}")
    
    # 调用统一的CBZ处理函数（会缓存所有图片）
    album = db.query(Album).filter(Album.id == album_id).first()
    if not album:
        raise HTTPException(status_code=404, detail="图集不存在")
    
    cbz_path = Path(album.file_path)
    if not cbz_path.exists():
        raise HTTPException(status_code=404, detail="CBZ文件不存在")
    
    image_list = ArchiveService.process_and_cache_cbz(cbz_path, album_id)
    
    # 从缓存中获取指定图片
    image_data = cache_service.get_extracted_image(album_id, filename)
    if not image_data:
        raise HTTPException(status_code=404, detail="图片不存在")
    
    # 缩放处理
    if width or height:
        image_data = ArchiveService.resize_image(image_data, width, height)
    
    from fastapi.responses import Response
    return Response(content=image_data, media_type="image/jpeg")

@router.post("/{album_id}/refresh")
async def refresh_album(album_id: int, db: Session = Depends(get_db)):
    """
    刷新指定图集的元数据
    """
    from ...services.scanner import extract_cbz_metadata
    
    album = db.query(Album).filter(Album.id == album_id).first()
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
async def get_cache_stats():
    """
    获取缓存统计信息
    """
    return cache_service.get_cache_stats()


@router.post("/cache/clear")
async def clear_cache(cache_type: str = "all"):
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
async def cleanup_expired_cache():
    """
    手动触发过期缓存清理
    """
    cache_service.cleanup_expired()
    return {
        "success": True,
        "message": "过期缓存清理完成"
    }