from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from pathlib import Path
from typing import Dict, Optional
import json
import asyncio
import uuid
import logging
import threading
from datetime import datetime

from app.database import get_db, SessionLocal
from app.models import User, ScanTask, Album
from app.schemas import ScanResponse
from app.services.scanner import scan_albums, cleanup_deleted_albums, cleanup_orphaned_data, get_orphaned_stats
from app.api.endpoints.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/scan", tags=["scan"])

# 进度回调注册表（线程安全）
_progress_callbacks: Dict[str, callable] = {}
_progress_callbacks_lock = threading.Lock()

# 存储事件循环引用供后台线程使用
_event_loop: Optional[asyncio.AbstractEventLoop] = None
_event_loop_lock = threading.Lock()


def set_event_loop(loop: asyncio.AbstractEventLoop):
    """设置事件循环引用"""
    global _event_loop
    with _event_loop_lock:
        _event_loop = loop


def get_event_loop_safe() -> Optional[asyncio.AbstractEventLoop]:
    """安全地获取事件循环"""
    with _event_loop_lock:
        return _event_loop


def register_progress_callback(task_id: str, callback: callable):
    """注册进度回调（线程安全）"""
    with _progress_callbacks_lock:
        _progress_callbacks[task_id] = callback


def unregister_progress_callback(task_id: str):
    """取消注册进度回调（线程安全）"""
    with _progress_callbacks_lock:
        _progress_callbacks.pop(task_id, None)


def get_progress_callback(task_id: str) -> Optional[callable]:
    """获取进度回调（线程安全）"""
    with _progress_callbacks_lock:
        return _progress_callbacks.get(task_id)


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


def _update_task_progress(task_id: str, data: Dict):
    """
    更新任务进度（线程安全，使用独立会话）
    
    Args:
        task_id: 任务ID
        data: 进度数据
    """
    db = SessionLocal()
    try:
        task = db.query(ScanTask).filter(ScanTask.task_id == task_id).first()
        if not task:
            return
        
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
        
    except Exception as e:
        db.rollback()
        logger.error(f"更新任务进度失败: {e}")
    finally:
        db.close()


def _notify_progress_callback(task_id: str, data: Dict):
    """
    通知 SSE 进度回调（线程安全）
    
    Args:
        task_id: 任务ID
        data: 进度数据
    """
    callback = get_progress_callback(task_id)
    if not callback:
        return
    
    loop = get_event_loop_safe()
    if not loop or loop.is_closed():
        logger.warning("事件循环不可用，跳过进度通知")
        return
    
    try:
        asyncio.run_coroutine_threadsafe(callback(data), loop)
    except Exception as e:
        logger.warning(f"通知进度回调失败: {e}")


def _run_scan_task(task_id: str, scan_path: Path, full_scan: bool):
    """执行扫描任务（在后台线程中运行）"""
    db = SessionLocal()
    try:
        # 获取任务
        task = db.query(ScanTask).filter(ScanTask.task_id == task_id).first()
        if not task:
            logger.error(f"任务不存在: {task_id}")
            return
        
        # 更新状态为运行中
        task.status = 'running'
        task.started_at = datetime.utcnow()
        db.commit()
        
        # 进度回调（使用独立会话更新数据库，使用事件循环通知 SSE）
        def progress_callback(data: Dict):
            try:
                # 使用独立会话更新数据库（线程安全）
                _update_task_progress(task_id, data)
                
                # 通知 SSE 回调（使用安全的事件循环获取）
                _notify_progress_callback(task_id, data)
                        
            except Exception as e:
                logger.error(f"进度回调处理失败: {e}")
        
        # 执行扫描
        results = scan_albums(db, scan_path, progress_callback=progress_callback)
        
        # 更新完成状态
        task.status = 'completed'
        task.processed_files = results['results']['scanned_files']
        task.new_albums = results['results']['new_albums']
        task.updated_albums = results['results']['updated_albums']
        task.completed_at = datetime.utcnow()
        db.commit()
        
        # 通知完成
        _notify_progress_callback(task_id, {
            'status': 'completed',
            'processed': task.processed_files,
            'new_albums': task.new_albums,
            'updated_albums': task.updated_albums
        })
        
        logger.info(f"扫描任务完成: {task_id}")
        
    except Exception as e:
        logger.error(f"扫描任务失败: {e}")
        
        # 更新失败状态（使用独立会话）
        fail_db = SessionLocal()
        try:
            task = fail_db.query(ScanTask).filter(ScanTask.task_id == task_id).first()
            if task:
                task.status = 'failed'
                task.error_message = str(e)
                task.completed_at = datetime.utcnow()
                fail_db.commit()
            
            # 通知失败
            _notify_progress_callback(task_id, {
                'status': 'failed',
                'error': str(e)
            })
        except Exception as inner_e:
            logger.error(f"更新失败状态失败: {inner_e}")
            fail_db.rollback()
        finally:
            fail_db.close()
        
    finally:
        db.close()
        # 清理回调
        unregister_progress_callback(task_id)


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
    
    # 使用数据库锁防止竞态条件
    # 先尝试获取一个排他锁，确保只有一个请求能创建任务
    try:
        # 使用 SQLite 的 IMMEDIATE 事务来获取锁
        db.execute(text("BEGIN IMMEDIATE"))
        
        # 检查是否有正在运行的任务
        running_task = get_running_task(db)
        if running_task:
            db.rollback()
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
            db.rollback()
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
        
    except Exception as e:
        db.rollback()
        logger.error(f"创建扫描任务失败: {e}")
        return ScanResponse(
            success=False,
            message=f"创建扫描任务失败: {str(e)}",
            scanned_files=0,
            new_albums=0,
            updated_albums=0
        )
    
    # 确保事件循环引用已设置
    try:
        loop = asyncio.get_running_loop()
        set_event_loop(loop)
    except RuntimeError:
        logger.warning("无法获取运行中的事件循环")
    
    # 启动后台线程执行扫描
    thread = threading.Thread(
        target=_run_scan_task,
        args=(task_id, scan_path, full_scan),
        daemon=True,
        name=f"scan-task-{task_id}"
    )
    thread.start()
    
    logger.info(f"扫描任务已启动: {task_id}")
    
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
    
    # 确保事件循环引用已设置
    try:
        loop = asyncio.get_running_loop()
        set_event_loop(loop)
    except RuntimeError:
        pass
    
    async def event_generator():
        # 使用独立会话获取任务状态
        status_db = SessionLocal()
        try:
            # 获取正在运行的任务
            task = get_running_task(status_db)
            
            if not task:
                # 检查是否有最新任务
                latest = get_latest_task(status_db)
                if latest:
                    yield f"data: {json.dumps(latest)}\n\n"
                else:
                    yield f"data: {json.dumps({'status': 'no_task'})}\n\n"
                return
            
            task_id = task.task_id
            
            # 创建队列用于接收进度更新
            queue: asyncio.Queue = asyncio.Queue()
            
            async def progress_callback(data: Dict):
                await queue.put(data)
            
            # 注册回调（线程安全）
            register_progress_callback(task_id, progress_callback)
            
            try:
                # 先发送当前状态
                current_status = get_latest_task(status_db)
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
                # 取消注册回调（线程安全）
                unregister_progress_callback(task_id)
                
        finally:
            status_db.close()
    
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


@router.post("/fix-covers")
async def fix_missing_covers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    修复缺失封面的图集
    
    检查并修复：
    1. file_path 错误时尝试查找正确的文件并修复
    2. cover_path 为空或封面文件不存在
    3. cover_path 文件名与 file_path stem 不匹配
    """
    from ...config import settings
    from ...services.scanner.cover_fixer import CoverFixer
    import threading
    
    # 检查是否有正在运行的任务
    running_task = get_running_task(db)
    if running_task:
        return {
            "success": False,
            "message": f"已有扫描任务在运行: {running_task.task_id}"
        }
    
    # 创建封面修复器并检测需要修复的图集
    cover_fixer = CoverFixer(
        db=db,
        covers_dir=Path(settings.COVERS_DIR),
        images_dir=Path(settings.IMAGES_DIR)
    )
    
    result = cover_fixer.detect_albums_need_fix()
    
    if result.count == 0:
        return {
            "success": True,
            "message": "没有需要修复的图集",
            "count": 0
        }
    
    # 创建修复任务
    task_id = str(uuid.uuid4())
    task = ScanTask(
        task_id=task_id,
        status='pending',
        scan_type='fix_covers',
        total_files=result.count,
        created_at=datetime.utcnow()
    )
    db.add(task)
    db.commit()
    
    # 获取需要修复的图集 ID 列表
    album_ids_needs_fix = result.album_ids_needs_fix.copy()
    
    def run_fix_covers():
        """执行封面修复（后台线程）"""
        from app.database import SessionLocal
        from app.services.scanner.cover_fixer import CoverFixer
        from app.config import settings
        
        task_db = SessionLocal()
        try:
            # 获取任务
            task = task_db.query(ScanTask).filter(ScanTask.task_id == task_id).first()
            if not task:
                return
            
            task.status = 'running'
            task.started_at = datetime.utcnow()
            task_db.commit()
            
            # 创建修复器
            fixer = CoverFixer(
                db=task_db,
                covers_dir=Path(settings.COVERS_DIR),
                images_dir=Path(settings.IMAGES_DIR)
            )
            
            processed = 0
            failed = 0
            
            # 修复每个图集
            for album_id in album_ids_needs_fix:
                try:
                    if fixer.fix_single_album(album_id):
                        processed += 1
                    else:
                        failed += 1
                    
                    # 更新任务进度
                    task.processed_files = processed
                    task.failed_files = failed
                    task_db.commit()
                    
                except Exception as e:
                    logger.error(f"修复封面失败 {album_id}: {e}")
                    failed += 1
                    task_db.rollback()
            
            # 完成任务
            task.status = 'completed'
            task.processed_files = processed
            task.failed_files = failed
            task.completed_at = datetime.utcnow()
            task_db.commit()
            
            logger.info(f"封面修复完成: 处理 {processed}, 失败 {failed}")
            
        except Exception as e:
            logger.error(f"封面修复任务失败: {e}")
            task = task_db.query(ScanTask).filter(ScanTask.task_id == task_id).first()
            if task:
                task.status = 'failed'
                task.error_message = str(e)
                task.completed_at = datetime.utcnow()
                task_db.commit()
        finally:
            task_db.close()
    
    # 启动后台线程
    thread = threading.Thread(target=run_fix_covers, daemon=True)
    thread.start()
    
    return {
        "success": True,
        "message": f"已启动封面修复任务，共 {result.count} 个图集",
        "count": result.count,
        "task_id": task_id,
        "reasons": result.get_reason_summary()
    }


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
