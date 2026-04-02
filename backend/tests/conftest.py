"""
测试配置和 fixtures
"""
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import os

from app.main import app
from app.database import Base, get_db
from app.models import Album, Tag, User, AlbumTag, Organization, Model


# 测试数据库 - 使用临时目录
TEST_DB_DIR = tempfile.mkdtemp()
TEST_DB_PATH = Path(TEST_DB_DIR) / "test.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """创建测试数据库会话"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """创建测试客户端"""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def test_album(db):
    """创建测试图集"""
    album = Album(
        title="测试图集",
        file_path="/test/album.cbz",
        file_name="album.cbz",
        image_count=10,
        is_active=1
    )
    db.add(album)
    db.commit()
    db.refresh(album)
    return album


@pytest.fixture
def test_album_with_cover(db):
    """创建带封面的测试图集"""
    album = Album(
        title="有封面的图集",
        file_path="/test/album_with_cover.cbz",
        file_name="album_with_cover.cbz",
        image_count=15,
        cover_path="/data/tmp/covers/album_with_cover.webp",
        cover_image="001.jpg",
        is_active=1
    )
    db.add(album)
    db.commit()
    db.refresh(album)
    return album


@pytest.fixture
def multiple_albums(db):
    """创建多个测试图集"""
    albums = []
    for i in range(10):
        album = Album(
            title=f"测试图集 {i+1}",
            file_path=f"/test/album_{i+1}.cbz",
            file_name=f"album_{i+1}.cbz",
            image_count=10 + i,
            is_active=1
        )
        db.add(album)
        albums.append(album)
    db.commit()
    for album in albums:
        db.refresh(album)
    return albums


@pytest.fixture
def test_tag(db):
    """创建测试标签"""
    tag = Tag(
        name="测试标签",
        type="tag",
        description="测试用标签",
        album_count=0
    )
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


@pytest.fixture
def test_album_with_tag(db, test_album, test_tag):
    """创建带标签的测试图集"""
    album_tag = AlbumTag(album_id=test_album.id, tag_id=test_tag.id)
    db.add(album_tag)
    test_tag.album_count = 1
    db.commit()
    db.refresh(test_album)
    return test_album


@pytest.fixture
def test_user(db):
    """创建测试用户"""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=pwd_context.hash("testpass"),
        is_active=1,
        is_admin=1
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_token(client, test_user):
    """获取管理员令牌"""
    response = client.post("/api/auth/login", json={
        "username": "testuser",
        "password": "testpass"
    })
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(admin_token):
    """获取认证头"""
    return {"Authorization": f"Bearer {admin_token}"}
