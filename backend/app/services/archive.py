import zipfile
import io
from pathlib import Path
from typing import Optional, List
from PIL import Image

from .cache import cache_service

class ArchiveService:
    """CBZ文件处理服务"""
    
    @staticmethod
    def process_and_cache_cbz(cbz_path: Path, album_id: int) -> List[str]:
        """处理CBZ文件：解压并缓存全部图片信息
        
        Args:
            cbz_path: CBZ文件路径
            album_id: 图集ID
        
        Returns:
            图片文件名列表
        """
        print(f"\n📦 [CBZ处理] 开始解压并缓存: {cbz_path.name}, album_id={album_id}")
        
        try:
            with zipfile.ZipFile(cbz_path, 'r') as archive:
                # 获取所有图片文件
                image_files = [f for f in archive.namelist()
                              if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
                
                if not image_files:
                    print(f"⚠️  [警告] CBZ文件中没有图片: {cbz_path.name}")
                    return []
                
                print(f"📊 [文件统计] 发现 {len(image_files)} 张图片")
                
                # 批量读取并缓存
                image_dict = {}
                for i, img_file in enumerate(image_files, 1):
                    try:
                        image_data = archive.read(img_file)
                        image_dict[img_file] = image_data
                        if i <= 3:  # 只显示前3个
                            print(f"   📄 读取 [{i}/{len(image_files)}]: {img_file} ({len(image_data)} bytes)")
                    except Exception as e:
                        print(f"   ❌ 读取失败 [{i}/{len(image_files)}]: {img_file} - {e}")
                        continue
                
                # 批量缓存图片
                if image_dict:
                    print(f"💾 [批量缓存] 开始保存 {len(image_dict)} 张图片到缓存...")
                    cached_count = cache_service.batch_cache_images(album_id, image_dict)
                    
                    # 缓存图片列表
                    cache_service.set_image_list(album_id, image_files)
                    
                    # 标记缓存完成
                    cache_service.mark_album_cache_complete(album_id)
                    
                    print(f"✅ [CBZ处理完成] {cbz_path.name} - {cached_count}/{len(image_files)} 张图片已缓存")
                    return image_files
                
                return []
        except Exception as e:
            print(f"❌ [CBZ处理失败] {cbz_path.name}: {e}")
            return []
    
    @staticmethod
    def extract_image(cbz_path: Path, filename: str) -> Optional[bytes]:
        """从CBZ中提取单张图片（无缓存，专注提取）
        
        Args:
            cbz_path: CBZ文件路径
            filename: 图片文件名
        
        Returns:
            图片数据，失败返回None
        """
        try:
            with zipfile.ZipFile(cbz_path, 'r') as archive:
                if filename in archive.namelist():
                    return archive.read(filename)
                else:
                    print(f"❌ [提取失败] 图片不存在: {filename}")
                    return None
        except Exception as e:
            print(f"❌ [提取失败] {cbz_path.name}: {e}")
            return None
    
    @staticmethod
    def get_image_list(cbz_path: Path) -> List[str]:
        """获取CBZ文件中的图片列表（无缓存，专注提取）
        
        Args:
            cbz_path: CBZ文件路径
        
        Returns:
            图片文件名列表
        """
        try:
            with zipfile.ZipFile(cbz_path, 'r') as archive:
                return sorted([f for f in archive.namelist()
                             if f.lower().endswith(('.jpg', '.png', '.jpeg'))])
        except Exception as e:
            print(f"❌ [读取列表失败] {cbz_path.name}: {e}")
            return []
    
    @staticmethod
    def resize_image(image_data: bytes, width: int = None, height: int = None) -> bytes:
        """调整图片大小（保持宽高比）"""
        if not width and not height:
            return image_data
        
        try:
            img = Image.open(io.BytesIO(image_data))
            
            # 计算保持宽高比的新尺寸
            original_width, original_height = img.width, img.height
            aspect_ratio = original_width / original_height
            
            if width and height:
                # 同时指定宽高时，按最大比例缩放，保持原始宽高比
                target_ratio = width / height
                if aspect_ratio > target_ratio:
                    # 原图更宽，以宽度为准
                    new_width = width
                    new_height = int(width / aspect_ratio)
                else:
                    # 原图更高，以高度为准
                    new_height = height
                    new_width = int(height * aspect_ratio)
            elif width:
                # 只指定宽度
                new_width = width
                new_height = int(width / aspect_ratio)
            elif height:
                # 只指定高度
                new_height = height
                new_width = int(height * aspect_ratio)
            
            # 缩放图片
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 转换为字节（提高质量）
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=95)
            return output.getvalue()
        except Exception as e:
            print(f"Error resizing image: {e}")
            return image_data
    
    @staticmethod
    def get_image_info(cbz_path: Path, filename: str) -> dict:
        """获取图片信息"""
        image_data = ArchiveService.extract_image(cbz_path, filename)
        if not image_data:
            return {}
        
        try:
            img = Image.open(io.BytesIO(image_data))
            return {
                'width': img.width,
                'height': img.height,
                'format': img.format,
                'size': len(image_data)
            }
        except Exception as e:
            print(f"Error getting image info: {e}")
            return {}