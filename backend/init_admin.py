#!/usr/bin/env python3
"""
初始化管理员账户脚本
使用方法: python init_admin.py
"""

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database import SessionLocal, init_db
from app.models import User

# 密码哈希配置
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return pwd_context.hash(password)


def init_admin_user():
    """初始化管理员账户"""
    # 初始化数据库
    init_db()
    
    # 创建数据库会话
    db: Session = SessionLocal()
    
    try:
        # 检查管理员是否已存在
        existing_admin = db.query(User).filter(User.username == "wwg").first()
        
        if existing_admin:
            print("管理员账户 'wwg' 已存在")
            return
        
        # 创建管理员账户
        admin_user = User(
            username="wwg",
            email="admin@girlatlas.com",
            hashed_password=get_password_hash("z19831207"),
            is_active=1,
            is_admin=1,
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("管理员账户初始化成功!")
        print(f"用户名: {admin_user.username}")
        print(f"邮箱: {admin_user.email}")
        print(f"用户ID: {admin_user.id}")
        print(f"管理员权限: {'是' if admin_user.is_admin else '否'}")
        
    except Exception as e:
        print(f"初始化管理员账户失败: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_admin_user()
