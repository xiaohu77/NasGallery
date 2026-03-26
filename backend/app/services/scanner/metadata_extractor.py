import zipfile
import json
import re
import logging
from pathlib import Path
from typing import Dict, Optional, List

from app.config import settings

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """元数据提取和解析器"""
    
    @staticmethod
    def extract_metadata_from_cbz(file_path: Path) -> Optional[Dict]:
        """
        从CBZ文件中提取metadata.json数据
        
        Returns:
            metadata dict 或 None (如果读取失败)
        """
        try:
            with zipfile.ZipFile(file_path, 'r') as archive:
                # 查找metadata.json文件
                metadata_files = [f for f in archive.namelist() if f.endswith('metadata.json')]
                if not metadata_files:
                    return None
                
                # 读取metadata.json
                metadata_content = archive.read(metadata_files[0]).decode('utf-8')
                metadata = json.loads(metadata_content)
                
                # 验证必要字段
                required_fields = ['institution', 'model', 'title', 'description']
                for field in required_fields:
                    if field not in metadata:
                        logger.warning(f"metadata.json缺少字段: {field}")
                
                return metadata
                
        except json.JSONDecodeError as e:
            logger.error(f"metadata.json格式错误: {file_path.name} - {e}")
            return None
        except Exception as e:
            logger.error(f"读取metadata失败: {file_path.name} - {e}")
            return None
    
    @staticmethod
    def parse_metadata_to_tags(metadata: Dict) -> Dict[str, List[str]]:
        """从metadata解析标签信息"""
        result = {'org': [], 'model': [], 'tags': []}
        
        try:
            # 1. 套图解析
            if 'institution' in metadata:
                institution = metadata['institution']
                org_name = re.sub(r'[A-Za-z]+', '', institution)
                if org_name:
                    result['org'].append(org_name)
            
            # 2. 模特解析
            if 'model' in metadata:
                model_name = metadata['model']
                if model_name:
                    result['model'].append(model_name)
            
            # 3. 通用标签解析
            title = metadata.get('title', '')
            description = metadata.get('description', '')
            combined_text = title + ' ' + description
            
            keywords = settings.TAG_KEYWORDS.split(',') if settings.TAG_KEYWORDS else []
            
            for keyword in keywords:
                if keyword in combined_text:
                    result['tags'].append(keyword)
                
        except Exception as e:
            logger.error(f"解析metadata标签失败: {e}")
        
        return result
    
    @staticmethod
    def parse_filename(filename: str) -> Dict[str, List[str]]:
        """从文件名解析标签信息（备用方案）- 只解析通用标签，不解析机构和模特"""
        try:
            name = filename.replace('.cbz', '')
            
            result = {'org': [], 'model': [], 'tags': []}
            
            # 通用标签解析
            keywords = settings.TAG_KEYWORDS.split(',') if settings.TAG_KEYWORDS else []
            
            for keyword in keywords:
                if keyword in name:
                    result['tags'].append(keyword)
                
        except Exception as e:
            logger.error(f"解析文件名失败 {filename}: {e}")
            result = {'org': [], 'model': [], 'tags': []}
        
        return result
    
    @staticmethod
    def parse_folder_name(folder_name: str) -> Dict[str, List[str]]:
        """从文件夹名解析标签信息（备用方案）- 只解析通用标签，不解析机构和模特"""
        try:
            result = {'org': [], 'model': [], 'tags': []}
            
            # 通用标签解析
            keywords = settings.TAG_KEYWORDS.split(',') if settings.TAG_KEYWORDS else []
            
            for keyword in keywords:
                if keyword in folder_name:
                    result['tags'].append(keyword)
            
            return result
            
        except Exception as e:
            logger.error(f"解析文件夹名失败 {folder_name}: {e}")
            return {'org': [], 'model': [], 'tags': []}
    
    @staticmethod
    def parse_path_structure(relative_path: str, scan_root: str) -> Dict[str, List[str]]:
        """从目录路径结构解析机构和模特信息
        
        支持的路径格式：
        - org/机构名/图集 → 添加机构标签
        - model/模特名/图集 → 添加模特标签
        - 其他路径 → 不添加机构/模特标签
        
        Args:
            relative_path: 相对于扫描根目录的路径（不包含文件名）
            scan_root: 扫描根目录
        
        Returns:
            标签信息字典
        """
        try:
            result = {'org': [], 'model': [], 'tags': []}
            
            # 获取相对路径（去掉扫描根目录）
            path_parts = Path(relative_path).parts
            
            if len(path_parts) >= 2:
                # 检查第一级目录是否是 org 或 model
                first_level = path_parts[0].lower()
                
                if first_level == 'org' and len(path_parts) >= 2:
                    # org/机构名/图集
                    org_name = path_parts[1]
                    if org_name and not org_name.startswith('.'):
                        result['org'].append(org_name)
                
                elif first_level == 'model' and len(path_parts) >= 2:
                    # model/模特名/图集
                    model_name = path_parts[1]
                    if model_name and not model_name.startswith('.'):
                        result['model'].append(model_name)
            
            return result
            
        except Exception as e:
            logger.error(f"解析路径结构失败 {relative_path}: {e}")
            return {'org': [], 'model': [], 'tags': []}
    
    @staticmethod
    def extract_folder_metadata(folder_path: Path) -> Dict:
        """提取文件夹图集元数据（图片列表和封面）"""
        try:
            # 获取图片文件列表
            image_extensions = {'.jpg', '.jpeg', '.png'}
            image_files = sorted([
                f.name for f in folder_path.iterdir()
                if f.is_file() and f.suffix.lower() in image_extensions
            ])
            
            # 确定封面
            cover_image = None
            if 'cover.jpg' in image_files:
                cover_image = 'cover.jpg'
            elif 'cover.jpeg' in image_files:
                cover_image = 'cover.jpeg'
            elif 'cover.png' in image_files:
                cover_image = 'cover.png'
            elif image_files:
                cover_image = image_files[0]
            
            return {
                'image_count': len(image_files),
                'cover_image': cover_image,
                'file_list': image_files
            }
        except Exception as e:
            logger.error(f"提取文件夹元数据失败: {e}")
            return {'image_count': 0, 'cover_image': None, 'file_list': []}
    
    @staticmethod
    def extract_metadata_from_folder(folder_path: Path) -> Optional[Dict]:
        """
        从文件夹中提取metadata.json数据
        
        Returns:
            metadata dict 或 None (如果读取失败)
        """
        try:
            metadata_file = folder_path / 'metadata.json'
            if not metadata_file.exists():
                return None
            
            # 读取metadata.json
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata_content = f.read()
            
            metadata = json.loads(metadata_content)
            
            # 验证必要字段
            required_fields = ['institution', 'model', 'title', 'description']
            for field in required_fields:
                if field not in metadata:
                    logger.warning(f"metadata.json缺少字段: {field}")
            
            return metadata
            
        except json.JSONDecodeError as e:
            logger.error(f"metadata.json格式错误: {folder_path.name} - {e}")
            return None
        except Exception as e:
            logger.error(f"读取文件夹metadata失败: {folder_path.name} - {e}")
            return None
    
    @staticmethod
    def extract_cbz_metadata(file_path: Path) -> Dict:
        """提取CBZ文件元数据（图片列表和封面）"""
        try:
            with zipfile.ZipFile(file_path, 'r') as archive:
                # 获取图片文件列表
                image_files = [f for f in archive.namelist()
                              if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
                image_files.sort()
                
                # 确定封面
                cover_image = None
                if 'cover.jpg' in image_files:
                    cover_image = 'cover.jpg'
                elif image_files:
                    cover_image = image_files[0]
                
                return {
                    'image_count': len(image_files),
                    'cover_image': cover_image,
                    'file_list': image_files
                }
        except Exception as e:
            logger.error(f"提取CBZ元数据失败: {e}")
            return {'image_count': 0, 'cover_image': None, 'file_list': []}
