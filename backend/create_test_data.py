#!/usr/bin/env python3
"""
创建文件夹图集测试数据
从 picsum.photos 下载免费测试图片
"""
import os
import sys
import urllib.request
import json
from pathlib import Path

# 测试数据目录
TEST_DATA_DIR = Path(__file__).parent / "data" / "images"

# 文件夹图集配置
FOLDER_ALBUMS = [
    {
        "name": "风景摄影__自然风光__张三",
        "description": "美丽的自然风景摄影作品",
        "image_count": 5,
        "cover": "cover.jpg"
    },
    {
        "name": "城市建筑__现代设计__李四",
        "description": "现代城市建筑摄影集",
        "image_count": 4,
        "cover": "cover.jpg"
    },
    {
        "name": "动物世界__野生动物__王五",
        "description": "野生动物摄影作品",
        "image_count": 6,
        "cover": None  # 使用第一张图片作为封面
    }
]

def download_image(url: str, save_path: Path, timeout: int = 30) -> bool:
    """下载图片"""
    try:
        print(f"  下载: {url}")
        urllib.request.urlretrieve(url, save_path)
        print(f"  保存: {save_path}")
        return True
    except Exception as e:
        print(f"  下载失败: {e}")
        return False

def create_folder_album(album_config: dict) -> bool:
    """创建文件夹图集"""
    album_name = album_config["name"]
    album_dir = TEST_DATA_DIR / album_name
    
    print(f"\n📁 创建文件夹图集: {album_name}")
    
    # 创建目录
    album_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建 metadata.json
    metadata = {
        "institution": album_name.split("__")[0] if "__" in album_name else album_name,
        "model": album_name.split("__")[2] if "__" in album_name and len(album_name.split("__")) > 2 else "",
        "title": album_name,
        "description": album_config.get("description", "")
    }
    
    metadata_path = album_dir / "metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"  创建 metadata.json: {metadata_path}")
    
    # 下载图片
    image_count = album_config["image_count"]
    cover_name = album_config.get("cover")
    
    for i in range(image_count):
        # 使用不同的图片ID来获取不同的图片
        # picsum.photos 的图片ID范围大约是 1-1000
        image_id = (hash(album_name) + i) % 900 + 100
        
        # 确定文件名
        if i == 0 and cover_name:
            filename = cover_name
        else:
            filename = f"{i+1:03d}.jpg"
        
        # 下载图片
        url = f"https://picsum.photos/id/{image_id}/800/600"
        save_path = album_dir / filename
        
        if not save_path.exists():
            download_image(url, save_path)
        else:
            print(f"  跳过已存在: {filename}")
    
    print(f"✅ 完成: {album_name}")
    return True

def main():
    """主函数"""
    print("🚀 开始创建文件夹图集测试数据")
    print(f"📁 数据目录: {TEST_DATA_DIR}")
    
    # 确保目录存在
    TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # 创建每个文件夹图集
    success_count = 0
    for album_config in FOLDER_ALBUMS:
        try:
            if create_folder_album(album_config):
                success_count += 1
        except Exception as e:
            print(f"❌ 创建失败: {album_config['name']} - {e}")
    
    print(f"\n📊 完成: {success_count}/{len(FOLDER_ALBUMS)} 个文件夹图集")
    print("\n💡 提示: 运行扫描命令测试新功能:")
    print("   curl -X POST http://localhost:8000/scan/sync")

if __name__ == '__main__':
    main()
