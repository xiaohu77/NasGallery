"""
工具函数测试
"""
import pytest
from app.utils import get_cover_url, paginate
from app.models import Album


class TestGetCoverUrl:
    """封面 URL 生成测试"""
    
    def test_with_cover_path(self):
        """测试有 cover_path 的情况"""
        album = Album(id=1, cover_path="/data/tmp/covers/test_file.webp")
        url = get_cover_url(album)
        assert url == "/covers/test_file.webp"
    
    def test_with_cover_image_only(self):
        """测试只有 cover_image 的情况"""
        album = Album(id=1, cover_image="001.jpg")
        url = get_cover_url(album)
        assert url == "/albums/1/images/001.jpg"
    
    def test_with_both_cover_path_and_image(self):
        """测试同时有 cover_path 和 cover_image（优先使用 cover_path）"""
        album = Album(
            id=1,
            cover_path="/data/tmp/covers/test.webp",
            cover_image="001.jpg"
        )
        url = get_cover_url(album)
        assert url == "/covers/test.webp"
    
    def test_with_no_cover(self):
        """测试无封面的情况"""
        album = Album(id=1)
        url = get_cover_url(album)
        assert url is None
    
    def test_with_chinese_filename(self):
        """测试中文文件名"""
        album = Album(
            id=1,
            cover_path="/data/tmp/covers/测试图集_001.webp"
        )
        url = get_cover_url(album)
        assert url == "/covers/测试图集_001.webp"


class TestPaginate:
    """分页函数测试"""
    
    def test_paginate_first_page(self):
        """测试第一页"""
        class MockQuery:
            def count(self):
                return 100
            
            def offset(self, n):
                self._offset = n
                return self
            
            def limit(self, n):
                self._limit = n
                return self
            
            def all(self):
                return [f"item_{i}" for i in range(min(self._limit, 100 - self._offset))]
        
        query = MockQuery()
        total, items = paginate(query, page=1, size=20)
        
        assert total == 100
        assert len(items) == 20
        assert query._offset == 0
    
    def test_paginate_middle_page(self):
        """测试中间页"""
        class MockQuery:
            def count(self):
                return 100
            
            def offset(self, n):
                self._offset = n
                return self
            
            def limit(self, n):
                self._limit = n
                return self
            
            def all(self):
                return [f"item_{i}" for i in range(min(self._limit, 100 - self._offset))]
        
        query = MockQuery()
        total, items = paginate(query, page=3, size=20)
        
        assert total == 100
        assert query._offset == 40  # (3-1) * 20
    
    def test_paginate_last_page(self):
        """测试最后一页"""
        class MockQuery:
            def count(self):
                return 100
            
            def offset(self, n):
                self._offset = n
                return self
            
            def limit(self, n):
                self._limit = n
                return self
            
            def all(self):
                remaining = 100 - self._offset
                return [f"item_{i}" for i in range(min(self._limit, remaining))]
        
        query = MockQuery()
        total, items = paginate(query, page=5, size=20)
        
        assert total == 100
        assert len(items) == 20
    
    def test_paginate_empty_result(self):
        """测试空结果"""
        class MockQuery:
            def count(self):
                return 0
            
            def offset(self, n):
                return self
            
            def limit(self, n):
                return self
            
            def all(self):
                return []
        
        query = MockQuery()
        total, items = paginate(query, page=1, size=20)
        
        assert total == 0
        assert items == []
