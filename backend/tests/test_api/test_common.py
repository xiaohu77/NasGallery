"""
健康检查和基础 API 测试
"""
import pytest


class TestHealth:
    """健康检查测试"""
    
    def test_health_check(self, client):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "app" in data


class TestCategories:
    """分类 API 测试"""
    
    def test_get_categories(self, client, auth_headers):
        """测试获取分类树（需要认证）"""
        response = client.get("/api/categories/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "org" in data
        assert "model" in data
        assert "tag" in data
    
    def test_get_tags(self, client, auth_headers, test_album_with_tag):
        """测试获取标签列表（需要认证，只返回 album_count > 0 的标签）"""
        response = client.get("/api/categories/tag", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # test_album_with_tag 关联了一个标签，album_count = 1
        assert len(data) >= 1
