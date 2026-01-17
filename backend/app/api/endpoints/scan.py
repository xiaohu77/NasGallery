from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pathlib import Path
from typing import Dict

from app.database import get_db
from app.models import User
from app.schemas import ScanResponse
from app.services.scanner import scan_albums, cleanup_deleted_albums, cleanup_orphaned_data, get_orphaned_stats
from app.api.endpoints.auth import get_current_user

router = APIRouter(prefix="/scan", tags=["scan"])

def perform_scan(db: Session, scan_path: Path = None):
    """执行扫描任务"""
    try:
        results = scan_albums(db, scan_path)
        return results
    except Exception as e:
        print(f"扫描失败: {e}")
        raise

@router.post("/", response_model=ScanResponse)
async def scan_albums_endpoint(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    full_scan: bool = False
):
    """
    扫描图集文件（后台任务）
    
    - full_scan: 是否完全重新扫描（忽略缓存）
    """
    from ...config import settings
    
    scan_path = settings.IMAGES_DIR
    
    if not scan_path.exists():
        return ScanResponse(
            success=False,
            message=f"扫描路径不存在: {scan_path}",
            scanned_files=0,
            new_albums=0,
            updated_albums=0
        )
    
    # 后台执行扫描
    background_tasks.add_task(perform_scan, db, scan_path)
    
    return ScanResponse(
        success=True,
        message="扫描任务已提交，正在后台执行",
        scanned_files=0,
        new_albums=0,
        updated_albums=0
    )

@router.post("/sync", response_model=ScanResponse)
async def scan_albums_sync(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    同步扫描图集文件（等待完成）
    """
    from ...config import settings
    
    scan_path = settings.IMAGES_DIR
    
    if not scan_path.exists():
        return ScanResponse(
            success=False,
            message=f"扫描路径不存在: {scan_path}",
            scanned_files=0,
            new_albums=0,
            updated_albums=0
        )
    
    # 同步执行扫描
    results = scan_albums(db, scan_path)
    
    return ScanResponse(
        success=True,
        message="扫描完成",
        scanned_files=results['results']['scanned_files'],
        new_albums=results['results']['new_albums'],
        updated_albums=results['results']['updated_albums']
    )


@router.post("/cleanup")
async def cleanup_data(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    清理已删除超过指定天数的图集记录
    
    Args:
        days: 删除超过多少天的记录（默认30天）
    """
    try:
        from ...services.cache import cache_service
        cleanup_deleted_albums(db, days, cache_service)
        return {
            "success": True,
            "message": f"已清理超过 {days} 天的删除记录"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"清理失败: {str(e)}"
        }


@router.post("/cleanup/orphans")
async def cleanup_orphans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    清理孤儿数据（孤立的标签和关联）
    """
    try:
        cleanup_orphaned_data(db)
        return {
            "success": True,
            "message": "孤儿数据清理完成"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"清理失败: {str(e)}"
        }


@router.get("/stats/orphans")
async def get_orphans_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """
    获取孤儿数据统计信息
    """
    return get_orphaned_stats(db)


@router.get("/stats")
async def get_scan_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """
    获取扫描统计信息
    """
    from ...services.scanner import get_scan_stats
    return get_scan_stats(db)