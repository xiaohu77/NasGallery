from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from typing import Optional
import json
import asyncio

from app.database import get_db
from app.services.ai import embedding_scanner, clip_service
from app.models import User

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.get("/status")
async def get_ai_status(db: Session = Depends(get_db)):
    """获取 AI 功能状态"""
    return {
        "available": clip_service.is_available(),
        "has_model_files": clip_service.has_model_files(),
        "model_info": clip_service.get_model_info(),
        "stats": embedding_scanner.get_scan_stats(db)
    }


@router.post("/scan")
async def start_ai_scan(
    use_gpu: bool = Query(True, description="是否使用 GPU"),
    db: Session = Depends(get_db)
):
    """启动 AI 向量扫描"""
    task_id = await embedding_scanner.start_scan(db, use_gpu)
    
    if task_id is None:
        # 检查是否已有任务在运行
        latest = embedding_scanner.get_latest_task(db)
        if latest and latest['status'] == 'running':
            return {
                "success": False,
                "message": "已有扫描任务在运行",
                "task_id": latest['task_id']
            }
        else:
            return {
                "success": False,
                "message": "CLIP 模型不可用，请先下载模型"
            }
    
    return {
        "success": True,
        "message": "扫描任务已启动",
        "task_id": task_id
    }


@router.get("/scan/status")
async def get_scan_status(
    task_id: Optional[str] = Query(None, description="任务ID"),
    db: Session = Depends(get_db)
):
    """获取扫描任务状态"""
    if task_id:
        status = embedding_scanner.get_task_status(db, task_id)
    else:
        status = embedding_scanner.get_latest_task(db)
    
    if status is None:
        return {"status": "no_task", "message": "没有扫描任务"}
    
    return status


@router.get("/scan/progress")
async def scan_progress_stream(db: Session = Depends(get_db)):
    """SSE 流式获取扫描进度"""
    
    async def event_generator():
        latest = embedding_scanner.get_latest_task(db)
        
        if not latest:
            yield f"data: {json.dumps({'status': 'no_task'})}\n\n"
            return
        
        task_id = latest['task_id']
        
        # 如果任务已完成或失败，直接返回状态
        if latest['status'] in ['completed', 'failed']:
            yield f"data: {json.dumps(latest)}\n\n"
            return
        
        # 创建队列用于接收进度更新
        queue = asyncio.Queue()
        
        async def progress_callback(data):
            await queue.put(data)
        
        # 注册回调
        embedding_scanner.register_progress_callback(task_id, progress_callback)
        
        try:
            # 先发送当前状态
            yield f"data: {json.dumps(latest)}\n\n"
            
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
            embedding_scanner.unregister_progress_callback(task_id)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/search")
async def ai_search(
    q: str = Query(..., description="搜索文本"),
    limit: int = Query(20, ge=1, le=500, description="每页数量"),
    page: int = Query(1, ge=1, description="页码"),
    min_similarity: float = Query(0.0, ge=0.0, le=1.0, description="最低相似度"),
    db: Session = Depends(get_db)
):
    """以文搜图集"""
    # 如果模型未加载，尝试自动加载
    if not clip_service.is_available():
        from fastapi.concurrency import run_in_threadpool
        success = await run_in_threadpool(clip_service.load_model, True)
        if not success:
            raise HTTPException(
                status_code=503, 
                detail="AI 搜索不可用，模型加载失败"
            )
    
    # 检查是否有向量数据
    from app.models import AlbumEmbedding
    embedding_count = db.query(AlbumEmbedding).count()
    
    if embedding_count == 0:
        raise HTTPException(
            status_code=400,
            detail="没有可用的向量数据，请先运行 AI 扫描"
        )
    
    # 获取所有匹配结果（不分页）
    all_results = await embedding_scanner.search_by_text(db, q, 500, min_similarity)
    total = len(all_results)
    
    # 分页
    start = (page - 1) * limit
    end = start + limit
    results = all_results[start:end]
    
    return {
        "query": q,
        "results": results,
        "total": total,
        "page": page,
        "size": limit,
        "has_more": end < total
    }


@router.post("/model/load")
async def load_model(
    use_gpu: bool = Query(True, description="是否使用 GPU"),
    provider: Optional[str] = Query(None, description="指定使用的提供程序")
):
    """加载 CLIP 模型（在后台线程中执行）"""
    # 在后台线池中执行，避免阻塞
    success = await run_in_threadpool(clip_service.load_model, use_gpu, provider)
    
    return {
        "success": success,
        "model_info": clip_service.get_model_info()
    }


@router.get("/providers")
async def get_providers():
    """获取可用的执行提供程序"""
    return clip_service.get_available_providers()


@router.post("/scan/pause")
async def pause_scan():
    """暂停扫描"""
    embedding_scanner.pause_scan()
    return {"success": True, "message": "扫描已暂停"}


@router.post("/scan/resume")
async def resume_scan():
    """恢复扫描"""
    embedding_scanner.resume_scan()
    return {"success": True, "message": "扫描已恢复"}
