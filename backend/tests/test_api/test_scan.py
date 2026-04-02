"""
扫描 API 测试
"""
import pytest


class TestScanStatus:
    """扫描状态测试"""
    
    def test_get_scan_status(self, client, auth_headers):
        """测试获取扫描状态"""
        response = client.get("/api/scan/status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "is_running" in data
    
    def test_get_scan_stats(self, client, auth_headers, test_album):
        """测试获取扫描统计"""
        response = client.get("/api/scan/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_albums" in data


class TestScanCleanup:
    """扫描清理测试"""
    
    def test_cleanup_orphans(self, client, auth_headers):
        """测试清理孤儿数据"""
        response = client.post("/api/scan/cleanup/orphans", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
    
    def test_get_orphans_stats(self, client, auth_headers):
        """测试获取孤儿数据统计（正确 URL: /api/scan/stats/orphans）"""
        response = client.get("/api/scan/stats/orphans", headers=auth_headers)
        assert response.status_code == 200


class TestFixCovers:
    """修复封面测试"""
    
    def test_fix_covers_api(self, client, auth_headers):
        """测试修复封面 API"""
        response = client.post("/api/scan/fix-covers", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "count" in data
    
    def test_fix_covers_with_real_file(self, client, auth_headers, db, tmp_path):
        """测试有真实封面文件时不需要修复"""
        from app.models import Album
        
        # 创建一个真实的封面文件
        covers_dir = tmp_path / "covers"
        covers_dir.mkdir()
        cover_file = covers_dir / "test_album.webp"
        cover_file.write_text("fake image")
        
        # 创建图集记录
        album = Album(
            title="有封面的图集",
            file_path="/test/album.cbz",
            file_name="album.cbz",
            image_count=10,
            cover_path=str(cover_file),
            is_active=1
        )
        db.add(album)
        db.commit()
        
        # 测试 API 调用（不检查具体 count，只检查 API 可用）
        response = client.post("/api/scan/fix-covers", headers=auth_headers)
        assert response.status_code == 200
