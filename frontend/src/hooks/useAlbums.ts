import { useState, useEffect, useCallback, useRef } from 'react';
import { PWAService } from '../services/pwaService';
import { AlbumSummary, AlbumCard } from '../types/album';

const API_BASE = import.meta.env.VITE_API_BASE || 'https://back.xiaohu777.cn';

export const useAlbums = (
  categoryType: 'org' | 'model' | 'tag' | null,
  categoryId: number | null,
  pwaService: PWAService
) => {
  const [albums, setAlbums] = useState<AlbumCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [scrollPosition, setScrollPosition] = useState<number>(0);

  const transformAlbum = useCallback((album: AlbumSummary): AlbumCard => {
    let coverImage = album.cover_url || '';

    if (coverImage && coverImage.startsWith('/')) {
      coverImage = `${API_BASE}${coverImage}`;
    }

    return {
      id: album.id.toString(),
      title: album.title,
      description: album.description || '暂无描述',
      coverImage: coverImage,
      imageCount: album.image_count
    };
  }, []);

  const fetchData = useCallback(async (pageNum: number = 1) => {
    try {
      setError(null);
      let response;

      if (categoryType && categoryId) {
        response = await pwaService.getAlbumsByCategory(categoryType, categoryId, pageNum, 20);
      } else {
        response = await pwaService.getAlbums(pageNum, 20);
      }

      if (response.page * response.size >= response.total) {
        setHasMore(false);
      } else {
        setHasMore(true);
      }

      const newAlbums = response.items.map(transformAlbum);

      if (pageNum === 1) {
        setAlbums(newAlbums);
      } else {
        setAlbums(prev => [...prev, ...newAlbums]);
      }

      return newAlbums;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '加载失败';
      setError(errorMessage);
      console.error('加载图集失败:', err);
      throw err;
    }
  }, [categoryType, categoryId, pwaService, transformAlbum]);

  // 保存滚动位置
  const saveScrollPosition = useCallback((position: number) => {
    setScrollPosition(position);
  }, []);

  const loadMore = useCallback(async () => {
    if (!hasMore || isLoadingMore || loading) return;

    setIsLoadingMore(true);
    const nextPage = page + 1;

    try {
      await fetchData(nextPage);
      setPage(nextPage);
    } catch (err) {
      console.error('加载更多失败:', err);
    } finally {
      setIsLoadingMore(false);
    }
  }, [hasMore, isLoadingMore, loading, page, fetchData]);

  const refresh = useCallback(async () => {
    setLoading(true);
    setPage(1);
    setHasMore(true);

    try {
      let response;

      if (categoryType && categoryId) {
        response = await pwaService.refreshAlbumsByCategory(categoryType, categoryId, 1, 20);
      } else {
        response = await pwaService.refreshAlbums(1, 20);
      }

      if (response.page * response.size >= response.total) {
        setHasMore(false);
      } else {
        setHasMore(true);
      }

      const newAlbums = response.items.map(transformAlbum);
      setAlbums(newAlbums);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '刷新失败';
      setError(errorMessage);
      console.error('刷新图集失败:', err);
    } finally {
      setLoading(false);
    }
  }, [categoryType, categoryId, pwaService, transformAlbum]);

  useEffect(() => {
    const loadInitialData = async () => {
      setLoading(true);
      setPage(1);
      setHasMore(true);
      setAlbums([]);

      try {
        await fetchData(1);
      } catch (err) {
        console.error('初始加载失败:', err);
      } finally {
        setLoading(false);
      }
    };

    loadInitialData();
  }, [fetchData]);

  return {
    albums,
    loading,
    error,
    page,
    hasMore,
    isLoadingMore,
    loadMore,
    refresh,
    scrollPosition,
    saveScrollPosition
  };
};