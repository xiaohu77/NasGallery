"""
任务相关模型
"""
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from .base import Base


class ScanTask(Base):
    """扫描任务状态表"""
    __tablename__ = "scan_tasks"
    
    id = Column(Integer, primary_key=True)
    task_id = Column(String, unique=True, nullable=False)  # UUID
    status = Column(String, default='pending')  # pending, running, completed, failed
    scan_type = Column(String, default='incremental')  # incremental, full, fix_covers
    total_files = Column(Integer, default=0)
    processed_files = Column(Integer, default=0)
    new_albums = Column(Integer, default=0)
    updated_albums = Column(Integer, default=0)
    failed_files = Column(Integer, default=0)
    current_file = Column(String)
    error_message = Column(String)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ScanTask(task_id='{self.task_id}', status='{self.status}')>"
