from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config import settings

# 创建数据库引擎
connect_args = {"check_same_thread": False}
if "sqlite" in settings.DATABASE_URL:
    connect_args.update({
        "timeout": 30,  # 设置SQLite超时为30秒
        "isolation_level": None  # 使用自动提交模式
    })

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,  # 禁用 SQLAlchemy 的详细 SQL 日志输出
    pool_pre_ping=True,  # 在使用连接前检查连接是否有效
    pool_recycle=3600,  # 定期回收连接
    pool_size=20,  # 连接池大小
    max_overflow=10  # 最大溢出连接数
)

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 从 models.base 导入 Base，保持一致
from .models.base import Base

# 依赖注入函数
def get_db():
    """
    数据库会话依赖注入
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    初始化数据库，创建所有表和索引
    """
    from .models import Album, Tag, Organization, Model, AlbumTag, User, AlbumEmbedding, AIScanTask, ScanTask, UserFavorite, UserHistory
    Base.metadata.create_all(bind=engine)
    
    # 创建额外的索引（如果不存在）
    from sqlalchemy import text
    with engine.connect() as conn:
        # Album 表索引
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_albums_is_active ON albums(is_active)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_albums_created_at ON albums(created_at)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_albums_title ON albums(title)"))
        
        # AlbumTag 表索引
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_album_tags_album_id ON album_tags(album_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_album_tags_tag_id ON album_tags(tag_id)"))
        
        # UserFavorite 表索引
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_favorites_user_id ON user_favorites(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_favorites_album_id ON user_favorites(album_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_favorites_user_album ON user_favorites(user_id, album_id)"))
        
        # UserHistory 表索引
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_history_user_id ON user_history(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_history_album_id ON user_history(album_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_history_viewed_at ON user_history(viewed_at)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_history_user_viewed ON user_history(user_id, viewed_at)"))
        
        # 为 Album 添加 view_count 列（如果不存在）
        try:
            conn.execute(text("ALTER TABLE albums ADD COLUMN view_count INTEGER DEFAULT 0"))
        except Exception:
            pass  # 列可能已存在
        
        conn.commit()
    
    print("数据库表和索引创建完成")

def drop_db():
    """
    删除所有表（用于测试）
    """
    from .models import Album, Tag, Organization, Model, AlbumTag
    Base.metadata.drop_all(bind=engine)
    print("数据库表删除完成")