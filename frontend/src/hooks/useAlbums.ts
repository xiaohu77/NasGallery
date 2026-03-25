import { useState, useEffect, useCallback, useRef } from 'react';
import { PWAService } from '../services/pwaService';
import { AlbumSummary, AlbumCard } from '../types/album';
import { sessionState, CacheKeys } from '../utils/cache';

const API_BASE = import.meta.env.DEV
  ? (import.meta.env.VITE_API_BASE || 'http://localhost:8000')
  : window.location.origin;

export const useAlbums = (
  categoryType: 'org' | 'model' | 'tag' | null,
  categoryId: number | null,
  pwaService: PWAService,
  searchQuery?: string
) => {
  // 生成状态键（包含搜索查询）
  const stateKey = CacheKeys.state.albums(categoryType, categoryId, searchQuery);
   
  // 使用ref来跟踪是否已经从缓存恢复
  const hasRestoredFromCache = useRef(false);
   
  // 从缓存恢复初始状态（只在组件挂载时执行一次）
  const getInitialState = () => {
    if (hasRestoredFromCache.current) {
      return {
        albums: [],
        loading: true,
        error: null,
        page: 1,
        hasMore: true,
        isLoadingMore: false,
        scrollPosition: 0
      };
    }
    
    const savedState = sessionState.get<{
      albums: AlbumCard[];
      page: number;
      hasMore: boolean;
      scrollPosition: number;
    }>(stateKey);
    
    // 如果有缓存数据，直接恢复（无有效期限制）
    if (savedState && savedState.albums.length > 0) {
      hasRestoredFromCache.current = true;
      return {
        albums: savedState.albums,
        loading: false,
        error: null,
        page: savedState.page,
        hasMore: savedState.hasMore,
        isLoadingMore: false,
        scrollPosition: savedState.scrollPosition
      };
    }
    
    return {
      albums: [],
      loading: true,
      error: null,
      page: 1,
      hasMore: true,
      isLoadingMore: false,
      scrollPosition: 0
    };
  };

  const initialState = getInitialState();
   
  const [albums, setAlbums] = useState<AlbumCard[]>(initialState.albums);
  const [loading, setLoading] = useState<boolean>(initialState.loading);
  const [error, setError] = useState<string | null>(initialState.error);
  const [page, setPage] = useState<number>(initialState.page);
  const [hasMore, setHasMore] = useState<boolean>(initialState.hasMore);
  const [isLoadingMore, setIsLoadingMore] = useState<boolean>(initialState.isLoadingMore);
  const [scrollPosition, setScrollPosition] = useState<number>(initialState.scrollPosition);
   
  // 保存状态到缓存
  const saveState = useCallback((currentAlbums: AlbumCard[], currentPage: number, currentHasMore: boolean, currentScrollPosition: number) => {
    sessionState.set(stateKey, {
      albums: currentAlbums,
      page: currentPage,
      hasMore: currentHasMore,
      scrollPosition: currentScrollPosition
    });
  }, [stateKey]);

  const transformAlbum = useCallback((album: AlbumSummary): AlbumCard => {
    let coverImage = album.cover_url || '';

    if (coverImage && coverImage.startsWith('/')) {
      // 如果封面URL以 /covers/ 开头，添加 /api 前缀
      if (coverImage.startsWith('/covers/')) {
        coverImage = `${API_BASE}/api${coverImage}`;
      } else {
        coverImage = `${API_BASE}${coverImage}`;
      }
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

      // 按标签类型筛选（如 org, model）
      if (categoryType && !categoryId) {
        response = await pwaService.getAlbums(pageNum, 20, categoryType);
      } else if (categoryType && categoryId) {
        response = await pwaService.getAlbumsByCategory(categoryType, categoryId, pageNum, 20);
      } else if (searchQuery) {
        response = await pwaService.searchAlbums(searchQuery, pageNum, 20);
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
        // 保存第一页状态
        saveState(newAlbums, 1, response.page * response.size < response.total, 0);
      } else {
        setAlbums(prev => {
          const updatedAlbums = [...prev, ...newAlbums];
          // 保存更多数据状态
          saveState(updatedAlbums, pageNum, response.page * response.size < response.total, scrollPosition);
          return updatedAlbums;
        });
      }

      return newAlbums;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '加载失败';
      setError(errorMessage);
      console.error('加载图集失败:', err);
      throw err;
    }
  }, [categoryType, categoryId, searchQuery, pwaService, transformAlbum, saveState, scrollPosition]);

  // 保存滚动位置
  const saveScrollPosition = useCallback((position: number) => {
    setScrollPosition(position);
    // 同时保存到缓存
    saveState(albums, page, hasMore, position);
  }, [albums, page, hasMore, saveState]);

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
    setAlbums([]);

    try {
      let response;

      // 按标签类型筛选（如 org, model）
      if (categoryType && !categoryId) {
        response = await pwaService.refreshAlbums(1, 20, categoryType);
      } else if (categoryType && categoryId) {
        response = await pwaService.refreshAlbumsByCategory(categoryType, categoryId, 1, 20);
      } else if (searchQuery) {
        response = await pwaService.searchAlbums(searchQuery, 1, 20);
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
      
      // 保存刷新后的状态
      saveState(newAlbums, 1, response.page * response.size < response.total, 0);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '刷新失败';
      setError(errorMessage);
      console.error('刷新图集失败:', err);
    } finally {
      setLoading(false);
    }
  }, [categoryType, categoryId, searchQuery, pwaService, transformAlbum, saveState]);

  // 当分类变化时，检查是否需要重新加载
  useEffect(() => {
    // 重置恢复标记，允许为新分类恢复缓存
    hasRestoredFromCache.current = false;
    
    const savedState = sessionState.get<{
      albums: AlbumCard[];
      page: number;
      hasMore: boolean;
      scrollPosition: number;
    }>(stateKey);
    
    // 如果有缓存数据，直接恢复
    if (savedState && savedState.albums.length > 0) {
      hasRestoredFromCache.current = true;
      setAlbums(savedState.albums);
      setPage(savedState.page);
      setHasMore(savedState.hasMore);
      setScrollPosition(savedState.scrollPosition);
      setLoading(false);
      return;
    }
    
    // 如果没有缓存数据，进行初始加载
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
  }, [fetchData, stateKey]);

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