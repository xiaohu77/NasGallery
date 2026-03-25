#!/usr/bin/env python3
"""
数据库迁移脚本：添加 album_type 字段到 albums 表
"""
import sqlite3
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def migrate():
    """执行数据库迁移"""
    from app.config import settings
    
    # 获取数据库路径
    # BASE_DIR 是 backend 目录
    db_path = settings.BASE_DIR / "data" / "nasgallery.db"
    
    print(f"数据库路径: {db_path}")
    
    if not db_path.exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    # 连接数据库
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # 检查 album_type 字段是否已存在
        cursor.execute("PRAGMA table_info(albums)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'album_type' in columns:
            print("✅ album_type 字段已存在，无需迁移")
            return
        
        # 添加 album_type 字段
        print("🔧 添加 album_type 字段...")
        cursor.execute("ALTER TABLE albums ADD COLUMN album_type VARCHAR DEFAULT 'cbz'")
        
        # 更新现有记录的 album_type 为 'cbz'
        print("🔧 更新现有记录的 album_type...")
        cursor.execute("UPDATE albums SET album_type = 'cbz' WHERE album_type IS NULL")
        
        conn.commit()
        print("✅ 数据库迁移完成")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 迁移失败: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
