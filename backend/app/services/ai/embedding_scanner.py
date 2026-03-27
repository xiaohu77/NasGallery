import logging
import uuid
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from sqlalchemy.orm import Session

from ...models import Album, AlbumEmbedding, AIScanTask
from .clip_service import clip_service, EMBEDDING_DIM

logger = logging.getLogger(__name__)


class EmbeddingScanner:
    """向量扫描服务 - 为图集生成嵌入向量"""
    
    def __init__(self):
        self.current_task_id: Optional[str] = None
        self._progress_callbacks: Dict[str, Callable] = {}
        self._is_paused: bool = False
        self._pause_lock = asyncio.Lock()
    
    def register_progress_callback(self, task_id: str, callback: Callable):
        """注册进度回调"""
        self._progress_callbacks[task_id] = callback
    
    def unregister_progress_callback(self, task_id: str):
        """取消注册进度回调"""
        if task_id in self._progress_callbacks:
            del self._progress_callbacks[task_id]
    
    def pause_scan(self):
        """暂停扫描"""
        self._is_paused = True
    
    def resume_scan(self):
        """恢复扫描"""
        self._is_paused = False
    
    async def _check_pause(self):
        """检查是否暂停"""
        while self._is_paused:
            await asyncio.sleep(0.5)
    
    async def _notify_progress(self, task_id: str, data: Dict[str, Any]):
        """通知进度更新"""
        if task_id in self._progress_callbacks:
            try:
                callback = self._progress_callbacks[task_id]
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception as e:
                logger.error(f"通知进度失败: {e}")
    
    async def start_scan(self, db: Session, use_gpu: bool = True) -> Optional[str]:
        """
        启动异步扫描任务
        
        Args:
            db: 数据库会话
            use_gpu: 是否使用 GPU
            
        Returns:
            任务ID，如果已有任务在运行则返回 None
        """
        # 检查是否有正在运行的任务
        running_task = db.query(AIScanTask).filter(
            AIScanTask.status == 'running'
        ).first()
        
        if running_task:
            logger.warning(f"已有扫描任务在运行: {running_task.task_id}")
            return None
        
        # 检查模型是否可用
        if not clip_service.is_available():
            # 尝试加载模型
            if not clip_service.load_model(use_gpu):
                logger.error("CLIP 模型不可用")
                return None
        
        # 创建新任务
        task_id = str(uuid.uuid4())
        task = AIScanTask(
            task_id=task_id,
            status='pending',
            created_at=datetime.utcnow()
        )
        db.add(task)
        db.commit()
        
        self.current_task_id = task_id
        
        # 启动后台任务
        asyncio.create_task(self._run_scan_task(task_id, db, use_gpu))
        
        logger.info(f"AI 扫描任务已启动: {task_id}")
        return task_id
    
    async def _run_scan_task(self, task_id: str, db: Session, use_gpu: bool):
        """执行扫描任务"""
        try:
            # 更新任务状态
            task = db.query(AIScanTask).filter(AIScanTask.task_id == task_id).first()
            if not task:
                return
            
            task.status = 'running'
            task.started_at = datetime.utcnow()
            db.commit()
            
            # 获取需要处理的图集
            albums = db.query(Album).filter(Album.is_active == 1).all()
            total = len(albums)
            
            task.total_albums = total
            db.commit()
            
            # 通知开始
            await self._notify_progress(task_id, {
                'task_id': task_id,
                'status': 'running',
                'total': total,
                'processed': 0,
                'failed': 0,
                'progress': 0,
                'message': '开始扫描...'
            })
            
            processed = 0
            failed = 0
            
            for album in albums:
                try:
                    # 检查是否暂停
                    await self._check_pause()
                    
                    # 检查是否已有向量
                    existing = db.query(AlbumEmbedding).filter(
                        AlbumEmbedding.album_id == album.id
                    ).first()
                    
                    if existing:
                        processed += 1
                        continue
                    
                    # 获取封面图片
                    cover_data = await self._get_cover_data(album)
                    if not cover_data:
                        logger.warning(f"无法获取封面: {album.id}")
                        failed += 1
                        continue
                    
                    # 编码图片 - 使用线程池执行CPU密集型操作
                    embedding = await asyncio.to_thread(clip_service.encode_image, cover_data)
                    if embedding is None:
                        logger.warning(f"编码失败: {album.id}")
                        failed += 1
                        continue
                    
                    # 保存向量
                    album_embedding = AlbumEmbedding(
                        album_id=album.id,
                        embedding=embedding.tobytes(),
                        model_version=clip_service.model_version,
                        created_at=datetime.utcnow()
                    )
                    db.add(album_embedding)
                    db.commit()
                    
                    processed += 1
                    
                    # 更新进度
                    progress = int((processed + failed) / total * 100)
                    await self._notify_progress(task_id, {
                        'task_id': task_id,
                        'status': 'running',
                        'total': total,
                        'processed': processed,
                        'failed': failed,
                        'progress': progress,
                        'message': f'已处理 {processed}/{total}'
                    })
                    
                    # 更新任务进度
                    task.processed_albums = processed
                    task.failed_albums = failed
                    db.commit()
                    
                    # 每处理完一个图片后让出CPU控制权，避免CPU满载
                    await asyncio.sleep(0)
                    
                except Exception as e:
                    logger.error(f"处理图集失败 {album.id}: {e}")
                    failed += 1
                    db.rollback()
                    await asyncio.sleep(0)
            
            # 任务完成
            task.status = 'completed'
            task.processed_albums = processed
            task.failed_albums = failed
            task.completed_at = datetime.utcnow()
            db.commit()
            
            await self._notify_progress(task_id, {
                'task_id': task_id,
                'status': 'completed',
                'total': total,
                'processed': processed,
                'failed': failed,
                'progress': 100,
                'message': f'扫描完成: 成功 {processed}, 失败 {failed}'
            })
            
            logger.info(f"AI 扫描任务完成: {task_id}")
            
        except Exception as e:
            logger.error(f"扫描任务异常: {e}")
            
            # 更新任务状态为失败
            task = db.query(AIScanTask).filter(AIScanTask.task_id == task_id).first()
            if task:
                task.status = 'failed'
                task.error_message = str(e)
                task.completed_at = datetime.utcnow()
                db.commit()
            
            await self._notify_progress(task_id, {
                'task_id': task_id,
                'status': 'failed',
                'error': str(e),
                'message': f'扫描失败: {e}'
            })
        
        finally:
            self.current_task_id = None
            self.unregister_progress_callback(task_id)
    
    async def _get_cover_data(self, album: Album) -> Optional[bytes]:
        """获取图集封面数据"""
        try:
            from ...services.cover import CoverService
            from ...config import settings
            
            if not album.file_path:
                return None
            
            cover_service = CoverService(settings.COVERS_DIR)
            album_path = Path(album.file_path)
            cover_path = cover_service.get_cover_path_by_cbz(album_path)
            
            if cover_path and cover_path.exists():
                with open(cover_path, 'rb') as f:
                    return f.read()
            
            return None
        except Exception as e:
            logger.error(f"获取封面数据失败: {e}")
            return None
    
    def get_task_status(self, db: Session, task_id: str) -> Optional[Dict]:
        """获取任务状态"""
        task = db.query(AIScanTask).filter(AIScanTask.task_id == task_id).first()
        if not task:
            return None
        
        return {
            'task_id': task.task_id,
            'status': task.status,
            'total': task.total_albums,
            'processed': task.processed_albums,
            'failed': task.failed_albums,
            'progress': int(task.processed_albums / task.total_albums * 100) if task.total_albums > 0 else 0,
            'error': task.error_message,
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None
        }
    
    def get_latest_task(self, db: Session) -> Optional[Dict]:
        """获取最新的任务状态"""
        task = db.query(AIScanTask).order_by(AIScanTask.created_at.desc()).first()
        if not task:
            return None
        
        return self.get_task_status(db, task.task_id)
    
    def get_scan_stats(self, db: Session) -> Dict:
        """获取扫描统计信息"""
        total_albums = db.query(Album).filter(Album.is_active == 1).count()
        embedded_albums = db.query(AlbumEmbedding).count()
        
        latest_task = self.get_latest_task(db)
        
        return {
            'total_albums': total_albums,
            'embedded_albums': embedded_albums,
            'pending_albums': total_albums - embedded_albums,
            'latest_task': latest_task,
            'model_info': clip_service.get_model_info()
        }
    
    async def search_by_text(self, db: Session, query: str, limit: int = 20) -> list:
        """
        以文搜图集
        
        Args:
            db: 数据库会话
            query: 搜索文本
            limit: 返回数量限制
            
        Returns:
            排序后的图集列表
        """
        if not clip_service.is_available():
            logger.error("CLIP 模型不可用")
            return []
        
        # 编码查询文本
        query_embedding = clip_service.encode_text(query)
        if query_embedding is None:
            logger.error("编码查询文本失败")
            return []
        
        # 获取所有图集向量
        embeddings = db.query(AlbumEmbedding).all()
        
        results = []
        for emb in embeddings:
            try:
                # 解析向量
                album_embedding = np.frombuffer(emb.embedding, dtype=np.float32)
                
                # 计算相似度
                similarity = clip_service.compute_similarity(query_embedding, album_embedding)
                
                # 获取图集信息
                album = db.query(Album).filter(Album.id == emb.album_id).first()
                if album and album.is_active == 1:
                    # 构造封面 URL（使用相对路径）
                    cover_url = ''
                    if album.cover_path:
                        from pathlib import Path
                        cover_name = Path(album.cover_path).name
                        cover_url = f'/covers/{cover_name}'
                    
                    results.append({
                        'album_id': album.id,
                        'title': album.title,
                        'cover_url': cover_url,
                        'image_count': album.image_count or 0,
                        'similarity': similarity
                    })
            except Exception as e:
                logger.error(f"计算相似度失败: {e}")
                continue
        
        # 按相似度排序
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return results[:limit]


# 需要导入 numpy
import numpy as np

# 全局实例
embedding_scanner = EmbeddingScanner()
