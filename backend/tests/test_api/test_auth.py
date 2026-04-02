"""
认证 API 测试
"""
import pytest


class TestLogin:
    """登录测试"""
    
    def test_login_success(self, client, test_user):
        """测试登录成功"""
        response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpass"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "testuser"
    
    def test_login_invalid_username(self, client, test_user):
        """测试用户名不存在"""
        response = client.post("/api/auth/login", json={
            "username": "nonexistent",
            "password": "testpass"
        })
        assert response.status_code == 401
    
    def test_login_invalid_password(self, client, test_user):
        """测试密码错误"""
        response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "wrongpass"
        })
        assert response.status_code == 401


class TestCurrentUser:
    """当前用户测试"""
    
    def test_get_current_user(self, client, auth_headers, test_user):
        """测试获取当前用户"""
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
    
    def test_get_current_user_unauthorized(self, client):
        """测试未认证（HTTPBearer 默认返回 403）"""
        response = client.get("/api/auth/me")
        # HTTPBearer 在没有凭证时返回 403 Forbidden
        assert response.status_code == 403
    
    def test_get_current_user_invalid_token(self, client):
        """测试无效令牌"""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
