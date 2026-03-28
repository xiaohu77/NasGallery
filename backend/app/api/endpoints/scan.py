from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pathlib import Path
from typing import Dict, Optional
import json
import asyncio
import uuid
from datetime import datetime

from app.database import get_db, SessionLocal
from app.models import User, ScanTask
from app.schemas import ScanResponse
from app.services.scanner import scan_albums, cleanup_deleted_albums, cleanup_orphaned_data, get_orphaned_stats
from app.api.endpoints.auth import get_current_user

router = APIRouter(prefix="/api/scan", tags=["scan"])

# 进度回调注册表
_progress_callbacks: Dict[str, callable] = {}


def get_running_task(db: Session) -> Optional[ScanTask]:
    """获取正在运行的任务"""
    return db.query(ScanTask).filter(ScanTask.status == 'running').first()


def get_latest_task(db: Session) -> Optional[Dict]:
    """获取最新任务状态"""
    task = db.query(ScanTask).order_by(ScanTask.created_at.desc()).first()
    if not task:
        return None
    
    return {
        'task_id': task.task_id,
        'status': task.status,
        'scan_type': task.scan_type,
        'total': task.total_files,
        'processed': task.processed_files,
        'new_albums': task.new_albums,
        'updated_albums': task.updated_albums,
        'failed': task.failed_files,
        'progress': int(task.processed_files / task.total_files * 100) if task.total_files > 0 else 0,
        'current_file': task.current_file,
        'error': task.error_message,
        'started_at': task.started_at.isoformat() if task.started_at else None,
        'completed_at': task.completed_at.isoformat() if task.completed_at else None
    }


def _run_scan_task(task_id: str, scan_path: Path, full_scan: bool):
    """执行扫描任务（在后台线程中运行）"""
    db = SessionLocal()
    try:
        # 获取任务
        task = db.query(ScanTask).filter(ScanTask.task_id == task_id).first()
        if not task:
            return
        
        # 更新状态为运行中
        task.status = 'running'
        task.started_at = datetime.utcnow()
        db.commit()
        
        # 进度回调
        def progress_callback(data: Dict):
            try:
                # 更新数据库中的任务状态
                if 'total' in data:
                    task.total_files = data.get('total', 0)
                if 'processed' in data:
                    task.processed_files = data.get('processed', 0)
                if 'new_albums' in data:
                    task.new_albums = data.get('new_albums', 0)
                if 'updated_albums' in data:
                    task.updated_albums = data.get('updated_albums', 0)
                if 'current_file' in data:
                    task.current_file = data.get('current_file', '')
                
                db.commit()
                
                # 通知 SSE 回调
                if task_id in _progress_callbacks:
                    callback = _progress_callbacks[task_id]
                    try:
                        # 使用 asyncio.run_coroutine_threadsafe 调用异步回调
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.run_coroutine_threadsafe(callback(data), loop)
                    except Exception:
                        pass
                        
            except Exception as e:
                db.rollback()
                print(f"更新进度失败: {e}")
        
        # 执行扫描（scan_albums 不支持 full_scan 参数，忽略它）
        results = scan_albums(db, scan_path, progress_callback=progress_callback)
        
        # 更新完成状态
        task.status = 'completed'
        task.processed_files = results['results']['scanned_files']
        task.new_albums = results['results']['new_albums']
        task.updated_albums = results['results']['updated_albums']
        task.completed_at = datetime.utcnow()
        db.commit()
        
        # 通知完成
        if task_id in _progress_callbacks:
            callback = _progress_callbacks[task_id]
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.run_coroutine_threadsafe(callback({
                        'status': 'completed',
                        'processed': task.processed_files,
                        'new_albums': task.new_albums,
                        'updated_albums': task.updated_albums
                    }), loop)
            except Exception:
                pass
        
    except Exception as e:
        # 更新失败状态
        task = db.query(ScanTask).filter(ScanTask.task_id == task_id).first()
        if task:
            task.status = 'failed'
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()
            db.commit()
        
        print(f"扫描任务失败: {e}")
        
    finally:
        db.close()


@router.post("/", response_model=ScanResponse)
async def scan_albums_endpoint(
    full_scan: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    扫描图集文件（异步后台任务）
    
    - full_scan: 是否完全重新扫描（忽略缓存）
    """
    from ...config import settings
    import threading
    
    # 检查是否有正在运行的任务
    running_task = get_running_task(db)
    if running_task:
        return ScanResponse(
            success=False,
            message=f"已有扫描任务在运行: {running_task.task_id}",
            scanned_files=0,
            new_albums=0,
            updated_albums=0,
            task_id=running_task.task_id
        )
    
    scan_path = settings.IMAGES_DIR
    
    if not scan_path.exists():
        return ScanResponse(
            success=False,
            message=f"扫描路径不存在: {scan_path}",
            scanned_files=0,
            new_albums=0,
            updated_albums=0
        )
    
    # 创建新任务
    task_id = str(uuid.uuid4())
    task = ScanTask(
        task_id=task_id,
        status='pending',
        scan_type='full' if full_scan else 'incremental',
        created_at=datetime.utcnow()
    )
    db.add(task)
    db.commit()
    
    # 启动后台线程执行扫描
    thread = threading.Thread(
        target=_run_scan_task,
        args=(task_id, scan_path, full_scan),
        daemon=True
    )
    thread.start()
    
    return ScanResponse(
        success=True,
        message="扫描任务已启动",
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


@router.get("/status")
async def get_scan_status(db: Session = Depends(get_db)):
    """获取当前扫描状态"""
    task = get_running_task(db)
    latest = get_latest_task(db)
    
    return {
        "is_running": task is not None,
        "running_task": get_running_task(db) and get_running_task(db).task_id,
        "latest_task": latest
    }


@router.get("/task/{task_id}")
async def get_task_status(task_id: str, db: Session = Depends(get_db)):
    """获取指定任务状态"""
    task = db.query(ScanTask).filter(ScanTask.task_id == task_id).first()
    if not task:
        return {"error": "任务不存在"}
    
    return {
        'task_id': task.task_id,
        'status': task.status,
        'scan_type': task.scan_type,
        'total': task.total_files,
        'processed': task.processed_files,
        'new_albums': task.new_albums,
        'updated_albums': task.updated_albums,
        'failed': task.failed_files,
        'progress': int(task.processed_files / task.total_files * 100) if task.total_files > 0 else 0,
        'current_file': task.current_file,
        'error': task.error_message,
        'started_at': task.started_at.isoformat() if task.started_at else None,
        'completed_at': task.completed_at.isoformat() if task.completed_at else None
    }


@router.get("/progress")
async def scan_progress_stream(db: Session = Depends(get_db)):
    """SSE 流式获取扫描进度"""
    
    async def event_generator():
        # 获取正在运行的任务
        task = get_running_task(db)
        
        if not task:
            # 检查是否有最新任务
            latest = get_latest_task(db)
            if latest:
                yield f"data: {json.dumps(latest)}\n\n"
            else:
                yield f"data: {json.dumps({'status': 'no_task'})}\n\n"
            return
        
        task_id = task.task_id
        
        # 创建队列用于接收进度更新
        queue = asyncio.Queue()
        
        async def progress_callback(data):
            await queue.put(data)
        
        # 注册回调
        _progress_callbacks[task_id] = progress_callback
        
        try:
            # 先发送当前状态
            current_status = get_latest_task(db)
            if current_status:
                yield f"data: {json.dumps(current_status)}\n\n"
            
            # 持续监听进度更新
            while True:
                try:
                    # 等待进度更新，超时30秒
                    data = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(data)}\n\n"
                    
                    # 如果任务完成或失败，结束流
                    if data.get('status') in ['completed', 'failed']:
                        break
                        
                except asyncio.TimeoutError:
                    # 发送心跳
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                    
        finally:
            # 取消注册回调
            if task_id in _progress_callbacks:
                del _progress_callbacks[task_id]
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/pause")
async def pause_scan():
    """暂停扫描（暂不支持）"""
    return {"success": False, "message": "图集扫描不支持暂停"}


@router.post("/cancel")
async def cancel_scan(db: Session = Depends(get_db)):
    """取消扫描"""
    task = get_running_task(db)
    if not task:
        return {"success": False, "message": "没有正在运行的扫描任务"}
    
    task.status = 'failed'
    task.error_message = '用户取消'
    task.completed_at = datetime.utcnow()
    db.commit()
    
    return {"success": True, "message": "扫描已取消"}


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
