import { useState, useEffect, useCallback, useRef } from 'react';
import { ImageItem } from '../types/album';
import { PWAService } from '../services/pwaService';

const API_BASE = import.meta.env.VITE_API_BASE || 'https://back.xiaohu777.cn';

interface LazyImagesResult {
  images: ImageItem[];
  loading: boolean;
  error: string | null;
  hasMore: boolean;
  loadMore: () => Promise<void>;
  refresh: () => Promise<void>;
  total: number;
  loadedCount: number;
}

export const useLazyImages = (
  albumId: string | undefined,
  pwaService: PWAService
): LazyImagesResult => {
  const [images, setImages] = useState<ImageItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState<boolean>(true);
  const [total, setTotal] = useState<number>(0);
  const [loadedCount, setLoadedCount] = useState<number>(0);

  const currentPage = useRef<number>(1);
  const isLoadingMore = useRef<boolean>(false);

  const transformImages = useCallback((items: any[], albumId: string, startIndex: number): ImageItem[] => {
    return items.map((img, index) => ({
      id: `${albumId}-${startIndex + index + 1}-${img.name}`,
      url: `${API_BASE}${img.url}`,
      title: `图片 ${startIndex + index + 1}`,
      description: img.name
    }));
  }, []);

  const loadImages = useCallback(async (page: number = 1, isRefresh: boolean = false) => {
    if (!albumId) {
      setLoading(false);
      return;
    }

    if (isLoadingMore.current && !isRefresh) return;

    isLoadingMore.current = true;
    setLoading(true);
    setError(null);

    try {
      const response = await pwaService.getAlbumImages(albumId, page, 3);

      const newImages = transformImages(response.images, albumId, (page - 1) * 3);

      if (isRefresh) {
        setImages(newImages);
        setLoadedCount(newImages.length);
      } else {
        setImages(prev => [...prev, ...newImages]);
        setLoadedCount(prev => prev + newImages.length);
      }

      setTotal(response.total);
      setHasMore(response.has_more);

      if (page === 1) {
        currentPage.current = 1;
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '加载图片失败';
      setError(errorMessage);
      console.error('加载图片失败:', err);
    } finally {
      setLoading(false);
      isLoadingMore.current = false;
    }
  }, [albumId, pwaService, transformImages]);

  const loadMore = useCallback(async () => {
    if (!hasMore || loading || isLoadingMore.current) return;

    currentPage.current += 1;
    await loadImages(currentPage.current, false);
  }, [hasMore, loading, loadImages]);

  const refresh = useCallback(async () => {
    if (!albumId) return;

    try {
      setLoading(true);
      setError(null);

      const response = await pwaService.refreshAlbumImages(albumId, 1, 3);

      const newImages = transformImages(response.images, albumId, 0);

      setImages(newImages);
      setLoadedCount(newImages.length);
      setTotal(response.total);
      setHasMore(response.has_more);
      currentPage.current = 1;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '刷新图片失败';
      setError(errorMessage);
      console.error('刷新图片失败:', err);
    } finally {
      setLoading(false);
    }
  }, [albumId, pwaService, transformImages]);

  useEffect(() => {
    if (albumId) {
      loadImages(1, true);
    }
  }, [albumId]);

  useEffect(() => {
    if (!albumId) {
      setImages([]);
      setTotal(0);
      setLoadedCount(0);
      setHasMore(true);
      currentPage.current = 1;
      setLoading(true);
    }
  }, [albumId]);

  return {
    images,
    loading,
    error,
    hasMore,
    loadMore,
    refresh,
    total,
    loadedCount
  };
};