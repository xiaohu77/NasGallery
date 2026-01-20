"""
静态文件服务端点
"""
from fastapi import APIRouter, HTTPException
from starlette.responses import FileResponse
from pathlib import Path
from urllib.parse import unquote

from app.config import settings

router = APIRouter(prefix="/api", tags=["static"])


@router.get("/covers/{cover_name}")
async def serve_cover(cover_name: str):
    """
    提供预提取的封面图（静态文件服务）
    cover_name: CBZ文件名.jpg，例如 XiuRen__No.10000__阿汁__75P.jpg
    """
    # URL解码文件名（处理中文字符等特殊字符）
    decoded_cover_name = unquote(cover_name)
    
    cover_path = settings.COVERS_DIR / decoded_cover_name
    
    if not cover_path.exists():
        raise HTTPException(status_code=404, detail="封面不存在")
    
    return FileResponse(
        cover_path,
        headers={
            "Cache-Control": "public, max-age=31536000",  # 1年缓存
            "ETag": f'"{cover_path.stat().st_mtime}"'
        }
    )


@router.get("/covers/stats")
async def cover_stats():
    """获取封面统计信息"""
    from app.services.cover import CoverService
    cover_service = CoverService(settings.COVERS_DIR)
    return cover_service.get_stats()
