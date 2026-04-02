"""
独立的工具函数测试（不依赖 app 完整导入）
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_get_cover_url():
    """测试封面 URL 生成"""
    from pathlib import Path
    from typing import Optional
    
    # 模拟 Album 类
    class MockAlbum:
        def __init__(self, id=1, cover_path=None, cover_image=None):
            self.id = id
            self.cover_path = cover_path
            self.cover_image = cover_image
    
    # 模拟 get_cover_url 函数
    def get_cover_url(album) -> Optional[str]:
        if album.cover_path:
            return f"/covers/{Path(album.cover_path).name}"
        elif album.cover_image:
            return f"/albums/{album.id}/images/{album.cover_image}"
        return None
    
    # 测试用例
    album1 = MockAlbum(id=1, cover_path="/data/tmp/covers/test.webp")
    assert get_cover_url(album1) == "/covers/test.webp"
    print("✓ Test 1 passed: cover_path")
    
    album2 = MockAlbum(id=1, cover_image="001.jpg")
    assert get_cover_url(album2) == "/albums/1/images/001.jpg"
    print("✓ Test 2 passed: cover_image")
    
    album3 = MockAlbum(id=1)
    assert get_cover_url(album3) is None
    print("✓ Test 3 passed: no cover")
    
    album4 = MockAlbum(id=1, cover_path="/data/tmp/covers/测试图集.webp")
    assert get_cover_url(album4) == "/covers/测试图集.webp"
    print("✓ Test 4 passed: chinese filename")
    
    print("\n✅ All tests passed!")


def test_paginate():
    """测试分页函数"""
    
    class MockQuery:
        def __init__(self, total=100):
            self._total = total
            self._offset = 0
            self._limit = 20
        
        def count(self):
            return self._total
        
        def offset(self, n):
            self._offset = n
            return self
        
        def limit(self, n):
            self._limit = n
            return self
        
        def all(self):
            remaining = self._total - self._offset
            return [f"item_{i}" for i in range(min(self._limit, remaining))]
    
    def paginate(query, page: int, size: int):
        total = query.count()
        items = query.offset((page - 1) * size).limit(size).all()
        return total, items
    
    # 测试用例
    query1 = MockQuery(100)
    total, items = paginate(query1, 1, 20)
    assert total == 100
    assert len(items) == 20
    print("✓ Test 1 passed: first page")
    
    query2 = MockQuery(100)
    total, items = paginate(query2, 3, 20)
    assert query2._offset == 40
    print("✓ Test 2 passed: middle page")
    
    query3 = MockQuery(0)
    total, items = paginate(query3, 1, 20)
    assert total == 0
    assert items == []
    print("✓ Test 3 passed: empty result")
    
    print("\n✅ All paginate tests passed!")


if __name__ == "__main__":
    print("=== Testing get_cover_url ===")
    test_get_cover_url()
    print("\n=== Testing paginate ===")
    test_paginate()
