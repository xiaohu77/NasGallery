from fastapi import APIRouter, Depends, HTTPException
from starlette.responses import FileResponse
from pathlib import Path

from app.config import settings

router = APIRouter(prefix="/api/thumbs", tags=["thumbs"])


@router.get("/{album_id}/{image_index}")
async def get_thumbnail(album_id: int, image_index: int) -> FileResponse:
    """返回指定专辑和图片序号的缩略图（WebP），文件命名约定：thumb_{album_id}_{index}_{stem}.webp"""
    thumbnail_dir: Path = settings.THUMBNAIL_DIR
    album_dir = thumbnail_dir / str(album_id)
    if not album_dir.exists():
        raise HTTPException(status_code=404, detail="缩略图目录不存在或未生成该专辑的缩略图")

    # 搜索匹配的文件，例如：thumb_42_3_某图片名.webp
    pattern = f"thumb_{album_id}_{image_index}_*.webp"
    matches = list(album_dir.glob(pattern))
    if not matches:
        raise HTTPException(status_code=404, detail="缩略图未就绪")

    # 仅返回第一个匹配的文件
    return FileResponse(matches[0], headers={"Cache-Control": "public, max-age=31536000"})
