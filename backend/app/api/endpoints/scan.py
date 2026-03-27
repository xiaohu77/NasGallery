from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pathlib import Path
from typing import Dict, Optional
import json
import asyncio
import uuid
from datetime import datetime

from app.database import get_db
from app.models import User
from app.schemas import ScanResponse
from app.services.scanner import scan_albums, cleanup_deleted_albums, cleanup_orphaned_data, get_orphaned_stats
from app.api.endpoints.auth import get_current_user

router = APIRouter(prefix="/api/scan", tags=["scan"])

# 全局扫描状态
_scan_task_id: Optional[str] = None
_scan_progress_callbacks: Dict[str, callable] = {}


async def _notify_scan_progress(task_id: str, data: Dict):
    """通知扫描进度"""
    if task_id in _scan_progress_callbacks:
        try:
            callback = _scan_progress_callbacks[task_id]
            if asyncio.iscoroutinefunction(callback):
                await callback(data)
            else:
                callback(data)
        except Exception as e:
            print(f"通知进度失败: {e}")


def perform_scan(db: Session, scan_path: Path = None, task_id: str = None):
    """执行扫描任务（带进度回调）"""
    from app.services.scanner import scan_albums
    try:
        async def async_progress_callback(data: Dict):
            if task_id and task_id in _scan_progress_callbacks:
                callback = _scan_progress_callbacks[task_id]
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    print(f"通知进度失败: {e}")
        
        def sync_progress_callback(data: Dict):
            if task_id and task_id in _scan_progress_callbacks:
                callback = _scan_progress_callbacks[task_id]
                try:
                    callback(data)
                except Exception as e:
                    print(f"通知进度失败: {e}")
        
        # 使用同步进度回调
        results = scan_albums(db, scan_path, progress_callback=sync_progress_callback)
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
    
    global _scan_task_id
    
    scan_path = settings.IMAGES_DIR
    
    if not scan_path.exists():
        return ScanResponse(
            success=False,
            message=f"扫描路径不存在: {scan_path}",
            scanned_files=0,
            new_albums=0,
            updated_albums=0
        )
    
    # 生成任务ID
    task_id = str(uuid.uuid4())
    _scan_task_id = task_id
    
    # 后台执行扫描
    background_tasks.add_task(perform_scan, db, scan_path, task_id)
    
    return ScanResponse(
        success=True,
        message="扫描任务已提交，正在后台执行",
        scanned_files=0,
        new_albums=0,
        updated_albums=0,
        task_id=task_id
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


@router.get("/progress")
async def scan_progress_stream():
    """SSE 流式获取扫描进度"""
    
    async def event_generator():
        global _scan_task_id
        
        if not _scan_task_id:
            yield f"data: {json.dumps({'status': 'no_task'})}\n\n"
            return
        
        task_id = _scan_task_id
        
        # 创建队列用于接收进度更新
        queue = asyncio.Queue()
        
        async def progress_callback(data):
            await queue.put(data)
        
        # 注册回调
        _scan_progress_callbacks[task_id] = progress_callback
        
        try:
            # 发送开始状态
            yield f"data: {json.dumps({'status': 'running', 'task_id': task_id})}\n\n"
            
            # 持续监听进度更新
            while True:
                try:
                    # 等待进度更新，超时30秒
                    data = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(data)}\n\n"
                    
                    # 如果任务完成，结束流
                    if data.get('status') in ['completed', 'failed']:
                        break
                        
                except asyncio.TimeoutError:
                    # 发送心跳
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                    
        finally:
            # 取消注册回调
            if task_id in _scan_progress_callbacks:
                del _scan_progress_callbacks[task_id]
            _scan_task_id = None
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/status")
async def get_scan_status():
    """获取当前扫描状态"""
    global _scan_task_id
    return {
        "is_running": _scan_task_id is not None,
        "task_id": _scan_task_id
    }