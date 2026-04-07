from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from app.database import get_db
from app.models import User, Album, UserFavorite, UserHistory, AlbumTag, Tag
from app.schemas import AlbumSummary, PagedResponse
from app.api.endpoints.auth import get_current_user
from app.utils import get_cover_url, paginate

router = APIRouter(prefix="/api/user", tags=["user"])


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


@router.get("/favorites", response_model=PagedResponse)
async def get_user_favorites(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的收藏列表"""
    query = db.query(Album).join(
        UserFavorite, UserFavorite.album_id == Album.id
    ).filter(
        UserFavorite.user_id == current_user.id,
        Album.is_active == 1
    ).order_by(UserFavorite.created_at.desc())
    
    from sqlalchemy.orm import joinedload
    query = query.options(joinedload(Album.tags))
    
    total, albums = paginate(query, page, size)
    items = [_build_album_summary(album) for album in albums]
    
    return PagedResponse(
        total=total,
        page=page,
        size=size,
        items=items
    )


@router.post("/favorites/{album_id}")
async def add_favorite(
    album_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """添加收藏"""
    album = db.query(Album).filter(
        Album.id == album_id,
        Album.is_active == 1
    ).first()
    if not album:
        raise HTTPException(status_code=404, detail="图集不存在")
    
    existing = db.query(UserFavorite).filter(
        UserFavorite.user_id == current_user.id,
        UserFavorite.album_id == album_id
    ).first()
    
    if existing:
        return {"success": True, "message": "已收藏", "is_favorited": True}
    
    favorite = UserFavorite(user_id=current_user.id, album_id=album_id)
    db.add(favorite)
    db.commit()
    
    return {"success": True, "message": "收藏成功", "is_favorited": True}


@router.delete("/favorites/{album_id}")
async def remove_favorite(
    album_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取消收藏"""
    favorite = db.query(UserFavorite).filter(
        UserFavorite.user_id == current_user.id,
        UserFavorite.album_id == album_id
    ).first()
    
    if not favorite:
        return {"success": True, "message": "未收藏", "is_favorited": False}
    
    db.delete(favorite)
    db.commit()
    
    return {"success": True, "message": "取消收藏成功", "is_favorited": False}


@router.get("/favorites/check/{album_id}")
async def check_favorite(
    album_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """检查是否已收藏"""
    favorite = db.query(UserFavorite).filter(
        UserFavorite.user_id == current_user.id,
        UserFavorite.album_id == album_id
    ).first()
    
    return {"is_favorited": favorite is not None}


@router.get("/history", response_model=PagedResponse)
async def get_user_history(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的浏览历史"""
    query = db.query(Album).join(
        UserHistory, UserHistory.album_id == Album.id
    ).filter(
        UserHistory.user_id == current_user.id,
        Album.is_active == 1
    ).order_by(UserHistory.viewed_at.desc())
    
    from sqlalchemy.orm import joinedload
    query = query.options(joinedload(Album.tags))
    
    total, albums = paginate(query, page, size)
    items = [_build_album_summary(album) for album in albums]
    
    return PagedResponse(
        total=total,
        page=page,
        size=size,
        items=items
    )


@router.post("/history/{album_id}")
async def add_history(
    album_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """记录浏览历史"""
    album = db.query(Album).filter(
        Album.id == album_id,
        Album.is_active == 1
    ).first()
    if not album:
        raise HTTPException(status_code=404, detail="图集不存在")
    
    existing = db.query(UserHistory).filter(
        UserHistory.user_id == current_user.id,
        UserHistory.album_id == album_id
    ).first()
    
    if existing:
        existing.viewed_at = datetime.utcnow()
    else:
        history = UserHistory(user_id=current_user.id, album_id=album_id)
        db.add(history)
    
    if album.view_count is None:
        album.view_count = 1
    else:
        album.view_count += 1
    
    db.commit()
    
    return {"success": True, "message": "浏览记录已更新"}


@router.delete("/history")
async def clear_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """清空浏览历史"""
    db.query(UserHistory).filter(
        UserHistory.user_id == current_user.id
    ).delete()
    db.commit()
    
    return {"success": True, "message": "浏览历史已清空"}


@router.get("/stats")
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户统计数据"""
    favorite_count = db.query(UserFavorite).filter(
        UserFavorite.user_id == current_user.id
    ).count()
    
    history_count = db.query(UserHistory).filter(
        UserHistory.user_id == current_user.id
    ).count()
    
    return {
        "favorite_count": favorite_count,
        "history_count": history_count
    }