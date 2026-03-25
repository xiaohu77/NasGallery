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
            
            # 默认标签
            if not result['org'] and not result['model'] and not result['tags']:
                result['tags'].append('默认')
                
        except Exception as e:
            logger.error(f"解析metadata标签失败: {e}")
            result['tags'].append('默认')
        
        return result
    
    @staticmethod
    def parse_filename(filename: str) -> Dict[str, List[str]]:
        """从文件名解析标签信息（备用方案）"""
        try:
            name = filename.replace('.cbz', '')
            parts = name.split('__')
            
            result = {'org': [], 'model': [], 'tags': []}
            
            # 1. 套图解析
            if len(parts) > 0:
                org_name = re.sub(r'[A-Za-z]+', '', parts[0])
                if org_name:
                    result['org'].append(org_name)
            
            # 2. 模特解析（改进版）
            # 模特字段通常在第3个位置（索引2），但需要排除页数格式
            if len(parts) > 2:
                potential_model = parts[2]
                # 检查是否是页数格式（如 75P, 80P, 100P 等）
                if not re.match(r'^\d+P$', potential_model):
                    # 检查是否是纯数字（可能是编号）
                    if not re.match(r'^\d+$', potential_model):
                        # 检查是否包含日期格式
                        if not re.match(r'^\d{4}\.\d{2}\.\d{2}$', potential_model):
                            result['model'].append(potential_model)
            
            # 3. 通用标签解析
            keywords = settings.TAG_KEYWORDS.split(',') if settings.TAG_KEYWORDS else []
            
            for keyword in keywords:
                if keyword in name:
                    result['tags'].append(keyword)
            
            # 默认标签
            if not result['org'] and not result['model'] and not result['tags']:
                result['tags'].append('默认')
                
        except Exception as e:
            logger.error(f"解析文件名失败 {filename}: {e}")
            result = {'org': [], 'model': [], 'tags': ['默认']}
        
        return result
    
    @staticmethod
    def parse_folder_name(folder_name: str) -> Dict[str, List[str]]:
        """从文件夹名解析标签信息（备用方案）"""
        try:
            # 如果文件夹名包含 __，则按 CBZ 命名规则解析
            if '__' in folder_name:
                return MetadataExtractor.parse_filename(folder_name)
            
            # 否则简单处理，使用文件夹名作为标题
            result = {'org': [], 'model': [], 'tags': ['默认']}
            
            # 尝试从文件夹名中提取套图信息
            name = folder_name
            org_name = re.sub(r'[A-Za-z]+', '', name)
            if org_name:
                result['org'].append(org_name)
            
            return result
            
        except Exception as e:
            logger.error(f"解析文件夹名失败 {folder_name}: {e}")
            return {'org': [], 'model': [], 'tags': ['默认']}
    
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
