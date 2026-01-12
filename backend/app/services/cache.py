import json
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from cachetools import TTLCache, LRUCache
import threading
import time

from ..config import settings


class CacheService:
    """缓存服务 - 提供文件缓存和内存缓存"""
    
    def __init__(self):
        # 缓存目录
        self.cache_dir = settings.CACHE_DIR
        self.image_lists_dir = self.cache_dir / "image_lists"
        self.extracted_images_dir = self.cache_dir / "extracted_images"
        self.metadata_dir = self.cache_dir / "metadata"
        
        # 确保缓存目录存在
        for directory in [self.image_lists_dir, self.extracted_images_dir, self.metadata_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # 内存缓存
        self.image_cache = LRUCache(maxsize=500)  # 图片内容，最多500张
        self.list_cache = TTLCache(maxsize=100, ttl=604800)  # 图片列表，7天过期
        self.metadata_cache = TTLCache(maxsize=100, ttl=604800)  # 元数据，7天过期
        
        # 缓存配置（统一为7天）
        self.image_list_ttl = timedelta(days=7)  # 图片列表缓存7天
        self.extracted_image_ttl = timedelta(days=7)  # 提取图片缓存7天
        self.metadata_ttl = timedelta(days=7)  # 元数据缓存7天
        
        # 清理锁
        self.cleanup_lock = threading.Lock()
        
        # 启动定时清理任务
        self._start_cleanup_timer()
    
    def _start_cleanup_timer(self):
        """启动定时清理任务（每天检查一次）"""
        def cleanup_worker():
            while True:
                time.sleep(86400)  # 每天检查一次（24小时 * 3600秒）
                self.cleanup_expired()
        
        thread = threading.Thread(target=cleanup_worker, daemon=True)
        thread.start()
    
    # ==================== 图片列表缓存 ====================
    
    def get_image_list(self, album_id: int) -> Optional[List[str]]:
        """从内存缓存获取图片列表"""
        cache_key = str(album_id)
        if cache_key in self.list_cache:
            return self.list_cache[cache_key]
        return None
    
    def get_image_list_from_file(self, album_id: int) -> Optional[List[str]]:
        """从文件缓存获取图片列表"""
        cache_file = self.image_lists_dir / f"{album_id}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            # 检查是否过期
            stat = cache_file.stat()
            file_time = datetime.fromtimestamp(stat.st_mtime)
            if datetime.now() - file_time > self.image_list_ttl:
                cache_file.unlink()
                return None
            
            # 读取缓存
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('images', [])
        except Exception:
            return None
    
    def set_image_list(self, album_id: int, images: List[str]):
        """缓存图片列表（同时保存到内存和文件）"""
        cache_file = self.image_lists_dir / f"{album_id}.json"
        
        try:
            data = {
                'images': images,
                'cached_at': datetime.now().isoformat()
            }
            # 保存到文件
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 同时缓存到内存
            self.list_cache[str(album_id)] = images
        except Exception as e:
            print(f"缓存图片列表失败: {e}")
    
    # ==================== 提取图片缓存 ====================
    
    def get_extracted_image(self, album_id: int, filename: str) -> Optional[bytes]:
        """获取缓存的提取图片（仅内存缓存）"""
        cache_key = f"{album_id}_{filename}"
        if cache_key in self.image_cache:
            return self.image_cache[cache_key]
        return None
    
    def set_extracted_image(self, album_id: int, filename: str, image_data: bytes):
        """缓存提取的图片（同时保存到内存和文件）"""
        cache_dir = self.extracted_images_dir / str(album_id)
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        image_file = cache_dir / filename
        
        try:
            # 保存到文件
            with open(image_file, 'wb') as f:
                f.write(image_data)
            
            # 同时缓存到内存
            cache_key = f"{album_id}_{filename}"
            self.image_cache[cache_key] = image_data
        except Exception as e:
            print(f"缓存图片失败: {e}")
    
    def batch_cache_images(self, album_id: int, image_dict: Dict[str, bytes]):
        """批量缓存图片（用于预解压整个CBZ）"""
        cache_dir = self.extracted_images_dir / str(album_id)
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        cached_count = 0
        for filename, image_data in image_dict.items():
            try:
                image_file = cache_dir / filename
                
                # 保存到文件
                with open(image_file, 'wb') as f:
                    f.write(image_data)
                
                # 同时缓存到内存
                cache_key = f"{album_id}_{filename}"
                self.image_cache[cache_key] = image_data
                
                cached_count += 1
            except Exception as e:
                print(f"批量缓存图片失败 {filename}: {e}")
        
        return cached_count
    
    def get_cached_album_images(self, album_id: int) -> Optional[List[str]]:
        """获取已缓存的图集图片列表（从文件系统）"""
        cache_dir = self.extracted_images_dir / str(album_id)
        if not cache_dir.exists():
            return None
        
        try:
            # 检查缓存是否过期
            cache_file = cache_dir / ".cache_info"
            if cache_file.exists():
                stat = cache_file.stat()
                file_time = datetime.fromtimestamp(stat.st_mtime)
                if datetime.now() - file_time > self.extracted_image_ttl:
                    # 缓存过期，清理目录
                    for file in cache_dir.iterdir():
                        if file.is_file():
                            file.unlink()
                    cache_dir.rmdir()
                    return None
            
            # 获取所有图片文件
            images = []
            for file in cache_dir.iterdir():
                if file.is_file() and file.suffix.lower() in ('.jpg', '.jpeg', '.png'):
                    images.append(file.name)
            
            return sorted(images) if images else None
        except Exception:
            return None
    
    def mark_album_cache_complete(self, album_id: int):
        """标记图集缓存完成"""
        cache_dir = self.extracted_images_dir / str(album_id)
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        cache_file = cache_dir / ".cache_info"
        try:
            with open(cache_file, 'w') as f:
                f.write(datetime.now().isoformat())
        except Exception as e:
            print(f"标记缓存完成失败: {e}")
    
    def is_album_cached(self, album_id: int) -> bool:
        """检查图集是否已完整缓存"""
        cache_dir = self.extracted_images_dir / str(album_id)
        if not cache_dir.exists():
            return False
        
        cache_file = cache_dir / ".cache_info"
        if not cache_file.exists():
            return False
        
        try:
            # 检查缓存是否过期
            stat = cache_file.stat()
            file_time = datetime.fromtimestamp(stat.st_mtime)
            if datetime.now() - file_time > self.extracted_image_ttl:
                return False
            
            # 检查是否有图片文件
            images = [f for f in cache_dir.iterdir()
                     if f.is_file() and f.suffix.lower() in ('.jpg', '.jpeg', '.png')]
            return len(images) > 0
        except Exception:
            return False
    
    # ==================== 元数据缓存 ====================
    
    def get_metadata(self, album_id: int) -> Optional[Dict[str, Any]]:
        """获取缓存的元数据"""
        cache_file = self.metadata_dir / f"{album_id}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            # 检查内存缓存
            cache_key = str(album_id)
            if cache_key in self.metadata_cache:
                return self.metadata_cache[cache_key]
            
            # 检查是否过期
            stat = cache_file.stat()
            file_time = datetime.fromtimestamp(stat.st_mtime)
            if datetime.now() - file_time > self.metadata_ttl:
                cache_file.unlink()
                return None
            
            # 读取缓存
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 更新内存缓存
            self.metadata_cache[cache_key] = data
            return data
        except Exception:
            return None
    
    def set_metadata(self, album_id: int, metadata: Dict[str, Any]):
        """缓存元数据"""
        cache_file = self.metadata_dir / f"{album_id}.json"
        
        try:
            data = {
                **metadata,
                'cached_at': datetime.now().isoformat()
            }
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 更新内存缓存
            self.metadata_cache[str(album_id)] = data
        except Exception as e:
            print(f"缓存元数据失败: {e}")
    
    # ==================== 缓存清理 ====================
    
    def cleanup_expired(self):
        """清理过期的缓存"""
        with self.cleanup_lock:
            current_time = datetime.now()
            cleaned_count = 0
            
            # 清理图片列表缓存
            for cache_file in self.image_lists_dir.glob("*.json"):
                try:
                    stat = cache_file.stat()
                    file_time = datetime.fromtimestamp(stat.st_mtime)
                    if current_time - file_time > self.image_list_ttl:
                        cache_file.unlink()
                        cleaned_count += 1
                except Exception:
                    pass
            
            # 清理提取图片缓存
            for album_dir in self.extracted_images_dir.iterdir():
                if album_dir.is_dir():
                    for image_file in album_dir.iterdir():
                        try:
                            stat = image_file.stat()
                            file_time = datetime.fromtimestamp(stat.st_mtime)
                            if current_time - file_time > self.extracted_image_ttl:
                                image_file.unlink()
                                cleaned_count += 1
                        except Exception:
                            pass
                    
                    # 如果目录为空，删除目录
                    if not any(album_dir.iterdir()):
                        album_dir.rmdir()
            
            # 清理元数据缓存
            for cache_file in self.metadata_dir.glob("*.json"):
                try:
                    stat = cache_file.stat()
                    file_time = datetime.fromtimestamp(stat.st_mtime)
                    if current_time - file_time > self.metadata_ttl:
                        cache_file.unlink()
                        cleaned_count += 1
                except Exception:
                    pass
            
            if cleaned_count > 0:
                print(f"清理了 {cleaned_count} 个过期缓存文件")
    
    def clear_cache(self, cache_type: str = "all"):
        """手动清除缓存"""
        with self.cleanup_lock:
            cleared_count = 0
            
            if cache_type in ["all", "lists"]:
                # 清除图片列表缓存
                for cache_file in self.image_lists_dir.glob("*.json"):
                    try:
                        cache_file.unlink()
                        cleared_count += 1
                    except Exception:
                        pass
                self.list_cache.clear()
            
            if cache_type in ["all", "images"]:
                # 清除提取图片缓存
                for album_dir in self.extracted_images_dir.iterdir():
                    if album_dir.is_dir():
                        for image_file in album_dir.iterdir():
                            try:
                                image_file.unlink()
                                cleared_count += 1
                            except Exception:
                                pass
                        album_dir.rmdir()
                self.image_cache.clear()
            
            if cache_type in ["all", "metadata"]:
                # 清除元数据缓存
                for cache_file in self.metadata_dir.glob("*.json"):
                    try:
                        cache_file.unlink()
                        cleared_count += 1
                    except Exception:
                        pass
                self.metadata_cache.clear()
            
            return cleared_count
    
    def clear_album_image_list(self, album_id: int):
        """清除指定图集的图片列表缓存"""
        cache_file = self.image_lists_dir / f"{album_id}.json"
        try:
            if cache_file.exists():
                cache_file.unlink()
            # 清除内存缓存
            if str(album_id) in self.list_cache:
                del self.list_cache[str(album_id)]
        except Exception as e:
            print(f"清除图片列表缓存失败: {e}")
    
    def clear_album_extracted_images(self, album_id: int):
        """清除指定图集的提取图片缓存"""
        cache_dir = self.extracted_images_dir / str(album_id)
        try:
            if cache_dir.exists():
                # 删除所有图片文件
                for file in cache_dir.iterdir():
                    if file.is_file():
                        file.unlink()
                # 删除目录
                cache_dir.rmdir()
            
            # 清除内存缓存（需要遍历删除）
            keys_to_remove = [k for k in self.image_cache.keys() if k.startswith(f"{album_id}_")]
            for key in keys_to_remove:
                del self.image_cache[key]
        except Exception as e:
            print(f"清除提取图片缓存失败: {e}")
    
    def clear_album_metadata(self, album_id: int):
        """清除指定图集的元数据缓存"""
        cache_file = self.metadata_dir / f"{album_id}.json"
        try:
            if cache_file.exists():
                cache_file.unlink()
            # 清除内存缓存
            if str(album_id) in self.metadata_cache:
                del self.metadata_cache[str(album_id)]
        except Exception as e:
            print(f"清除元数据缓存失败: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        stats = {
            'image_lists': {
                'file_count': len(list(self.image_lists_dir.glob("*.json"))),
                'memory_count': len(self.list_cache)
            },
            'extracted_images': {
                'file_count': sum(1 for _ in self.extracted_images_dir.rglob("*") if _.is_file()),
                'memory_count': len(self.image_cache)
            },
            'metadata': {
                'file_count': len(list(self.metadata_dir.glob("*.json"))),
                'memory_count': len(self.metadata_cache)
            }
        }
        
        # 计算磁盘使用情况
        total_size = 0
        for directory in [self.image_lists_dir, self.extracted_images_dir, self.metadata_dir]:
            for file in directory.rglob("*"):
                if file.is_file():
                    total_size += file.stat().st_size
        
        stats['disk_usage_mb'] = round(total_size / (1024 * 1024), 2)
        
        return stats


# 全局缓存实例
cache_service = CacheService()