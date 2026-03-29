from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
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

# 声明基类
Base = declarative_base()

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
    from .models import Album, Tag, Organization, Model, AlbumTag, User, AlbumEmbedding, AIScanTask, ScanTask
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
        
        conn.commit()
    
    print("数据库表和索引创建完成")

def drop_db():
    """
    删除所有表（用于测试）
    """
    from .models import Album, Tag, Organization, Model, AlbumTag
    Base.metadata.drop_all(bind=engine)
    print("数据库表删除完成")