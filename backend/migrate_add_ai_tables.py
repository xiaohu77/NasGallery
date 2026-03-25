#!/usr/bin/env python3
"""
数据库迁移脚本：添加 AI 搜索相关表
- album_embeddings: 图集向量表
- ai_scan_tasks: AI扫描任务状态表
"""
import sqlite3
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def migrate():
    """执行数据库迁移"""
    from app.config import settings
    
    # 获取数据库路径
    db_path = settings.BASE_DIR / "data" / "nasgallery.db"
    
    print(f"数据库路径: {db_path}")
    
    if not db_path.exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    # 连接数据库
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # 检查 album_embeddings 表是否已存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='album_embeddings'")
        if cursor.fetchone():
            print("✅ album_embeddings 表已存在")
        else:
            # 创建 album_embeddings 表
            print("🔧 创建 album_embeddings 表...")
            cursor.execute("""
                CREATE TABLE album_embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    album_id INTEGER NOT NULL UNIQUE,
                    embedding BLOB NOT NULL,
                    model_version VARCHAR DEFAULT 'clip-v1',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (album_id) REFERENCES albums (id)
                )
            """)
            print("✅ album_embeddings 表创建成功")
        
        # 检查 ai_scan_tasks 表是否已存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_scan_tasks'")
        if cursor.fetchone():
            print("✅ ai_scan_tasks 表已存在")
        else:
            # 创建 ai_scan_tasks 表
            print("🔧 创建 ai_scan_tasks 表...")
            cursor.execute("""
                CREATE TABLE ai_scan_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id VARCHAR NOT NULL UNIQUE,
                    status VARCHAR DEFAULT 'pending',
                    total_albums INTEGER DEFAULT 0,
                    processed_albums INTEGER DEFAULT 0,
                    failed_albums INTEGER DEFAULT 0,
                    error_message VARCHAR,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ ai_scan_tasks 表创建成功")
        
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
