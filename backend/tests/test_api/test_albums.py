"""
图集 API 测试
"""
import pytest


class TestAlbumsList:
    """图集列表测试"""
    
    def test_get_albums_empty(self, client):
        """测试空列表"""
        response = client.get("/api/albums/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []
    
    def test_get_albums_list(self, client, test_album):
        """测试获取图集列表"""
        response = client.get("/api/albums/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "测试图集"
    
    def test_get_albums_pagination(self, client, multiple_albums):
        """测试分页"""
        # 第一页
        response = client.get("/api/albums/?page=1&size=5")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 10
        assert len(data["items"]) == 5
        assert data["page"] == 1
        
        # 第二页
        response = client.get("/api/albums/?page=2&size=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5
        assert data["page"] == 2
    
    def test_get_albums_search(self, client, multiple_albums):
        """测试搜索"""
        response = client.get("/api/albums/?search=图集 1")
        assert response.status_code == 200
        data = response.json()
        # 应该找到包含 "图集 1" 的图集
        assert data["total"] >= 1


class TestAlbumDetail:
    """图集详情测试"""
    
    def test_get_album_detail(self, client, test_album):
        """测试获取图集详情"""
        response = client.get(f"/api/albums/{test_album.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_album.id
        assert data["title"] == "测试图集"
    
    def test_get_album_not_found(self, client):
        """测试图集不存在"""
        response = client.get("/api/albums/99999")
        assert response.status_code == 404


class TestAlbumCover:
    """图集封面测试"""
    
    def test_album_summary_cover_url(self, client, test_album_with_cover):
        """测试列表中封面 URL 生成"""
        response = client.get("/api/albums/")
        assert response.status_code == 200
        data = response.json()
        
        album_data = data["items"][0]
        assert album_data["cover_url"] == "/covers/album_with_cover.webp"
    
    def test_album_without_cover(self, client, test_album):
        """测试无封面的图集"""
        response = client.get("/api/albums/")
        assert response.status_code == 200
        data = response.json()
        
        album_data = data["items"][0]
        # 无封面时 cover_url 应该为 None
        assert album_data["cover_url"] is None


class TestAlbumsByTag:
    """按标签筛选图集测试"""
    
    def test_get_albums_by_tag(self, client, test_album_with_tag):
        """测试按标签筛选"""
        tag_id = test_album_with_tag.tags[0].id
        response = client.get(f"/api/albums/tag/{tag_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
    
    def test_get_albums_by_tag_not_found(self, client):
        """测试标签不存在"""
        response = client.get("/api/albums/tag/99999")
        assert response.status_code == 404
