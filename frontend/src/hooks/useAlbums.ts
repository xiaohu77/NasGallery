import { useReducer, useEffect, useCallback, useRef } from 'react';
import { PWAService } from '../services/pwaService';
import { AlbumSummary, AlbumCard } from '../types/album';
import { sessionState, CacheKeys } from '../utils/cache';

const API_BASE = import.meta.env.DEV
  ? (import.meta.env.VITE_API_BASE || 'http://localhost:8000')
  : window.location.origin;

interface AlbumsState {
  albums: AlbumCard[];
  loading: boolean;
  error: string | null;
  page: number;
  hasMore: boolean;
  isLoadingMore: boolean;
  scrollPosition: number;
}

type AlbumsAction =
  | { type: 'RESTORE_CACHE'; payload: { albums: AlbumCard[]; page: number; hasMore: boolean; scrollPosition: number } }
  | { type: 'START_LOADING' }
  | { type: 'LOAD_SUCCESS'; payload: { albums: AlbumCard[]; page: number; hasMore: boolean } }
  | { type: 'LOAD_MORE_SUCCESS'; payload: { albums: AlbumCard[]; page: number; hasMore: boolean } }
  | { type: 'LOAD_ERROR'; payload: string }
  | { type: 'START_LOAD_MORE' }
  | { type: 'SET_SCROLL'; payload: number }
  | { type: 'REFRESH' };

const initialState: AlbumsState = {
  albums: [],
  loading: true,
  error: null,
  page: 1,
  hasMore: true,
  isLoadingMore: false,
  scrollPosition: 0,
};

function albumsReducer(state: AlbumsState, action: AlbumsAction): AlbumsState {
  switch (action.type) {
    case 'RESTORE_CACHE':
      return {
        ...state,
        albums: action.payload.albums,
        page: action.payload.page,
        hasMore: action.payload.hasMore,
        scrollPosition: action.payload.scrollPosition,
        loading: false,
        error: null,
      };
    case 'START_LOADING':
      return { ...state, loading: true, error: null };
    case 'LOAD_SUCCESS':
      return {
        ...state,
        albums: action.payload.albums,
        page: action.payload.page,
        hasMore: action.payload.hasMore,
        loading: false,
        error: null,
      };
    case 'LOAD_MORE_SUCCESS':
      return {
        ...state,
        albums: [...state.albums, ...action.payload.albums],
        page: action.payload.page,
        hasMore: action.payload.hasMore,
        isLoadingMore: false,
      };
    case 'LOAD_ERROR':
      return { ...state, error: action.payload, loading: false, isLoadingMore: false };
    case 'START_LOAD_MORE':
      return { ...state, isLoadingMore: true };
    case 'SET_SCROLL':
      return { ...state, scrollPosition: action.payload };
    case 'REFRESH':
      return { ...initialState, loading: true };
    default:
      return state;
  }
}

export const useAlbums = (
  categoryType: 'org' | 'model' | 'cosplayer' | 'character' | 'tag' | null,
  categoryId: number | null,
  pwaService: PWAService,
  searchQuery?: string
) => {
  const stateKey = CacheKeys.state.albums(categoryType, categoryId, searchQuery);
  const [state, dispatch] = useReducer(albumsReducer, initialState);
  const stateRef = useRef(state);
  stateRef.current = state;

  // 保存状态到缓存
  const saveState = useCallback((albums: AlbumCard[], page: number, hasMore: boolean, scrollPosition: number) => {
    sessionState.set(stateKey, { albums, page, hasMore, scrollPosition });
  }, [stateKey]);

  const transformAlbum = useCallback((album: AlbumSummary): AlbumCard => {
    let coverImage = album.cover_url || '';
    if (coverImage.startsWith('/')) {
      coverImage = coverImage.startsWith('/covers/')
        ? `${API_BASE}/api${coverImage}`
        : `${API_BASE}${coverImage}`;
    }
    return {
      id: album.id.toString(),
      title: album.title,
      description: album.description || '暂无描述',
      coverImage,
      imageCount: album.image_count,
    };
  }, []);

  const fetchData = useCallback(async (pageNum: number) => {
    try {
      let response;
      if (categoryType && !categoryId) {
        response = await pwaService.getAlbums(pageNum, 20, categoryType);
      } else if (categoryType && categoryId) {
        response = await pwaService.getAlbumsByCategory(categoryType, categoryId, pageNum, 20);
      } else if (searchQuery) {
        response = await pwaService.searchAlbums(searchQuery, pageNum, 20);
      } else {
        response = await pwaService.getAlbums(pageNum, 20);
      }
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '加载失败';
      throw new Error(errorMessage);
    }
  }, [categoryType, categoryId, searchQuery, pwaService]);

  // 保存滚动位置（只更新缓存，不触发重渲染）
  const saveScrollPosition = useCallback((position: number) => {
    const { albums, page, hasMore } = stateRef.current;
    sessionState.set(stateKey, { albums, page, hasMore, scrollPosition: position });
  }, [stateKey]);

  const loadMore = useCallback(async () => {
    const { hasMore, isLoadingMore, loading, page } = stateRef.current;
    if (!hasMore || isLoadingMore || loading) return;

    dispatch({ type: 'START_LOAD_MORE' });
    try {
      const response = await fetchData(page + 1);
      const newAlbums = response.items.map(transformAlbum);
      const hasMoreData = response.page * response.size < response.total;
      dispatch({ type: 'LOAD_MORE_SUCCESS', payload: { albums: newAlbums, page: page + 1, hasMore: hasMoreData } });
      // 保存到缓存
      const updatedAlbums = [...stateRef.current.albums, ...newAlbums];
      saveState(updatedAlbums, page + 1, hasMoreData, stateRef.current.scrollPosition);
    } catch (err) {
      console.error('加载更多失败:', err);
      dispatch({ type: 'LOAD_ERROR', payload: err instanceof Error ? err.message : '加载失败' });
    }
  }, [fetchData, transformAlbum, saveState]);

  const refresh = useCallback(async () => {
    dispatch({ type: 'REFRESH' });
    try {
      let response;
      if (categoryType && !categoryId) {
        response = await pwaService.refreshAlbums(1, 20, categoryType);
      } else if (categoryType && categoryId) {
        response = await pwaService.refreshAlbumsByCategory(categoryType, categoryId, 1, 20);
      } else if (searchQuery) {
        response = await pwaService.searchAlbums(searchQuery, 1, 20);
      } else {
        response = await pwaService.refreshAlbums(1, 20);
      }
      const newAlbums = response.items.map(transformAlbum);
      const hasMoreData = response.page * response.size < response.total;
      dispatch({ type: 'LOAD_SUCCESS', payload: { albums: newAlbums, page: 1, hasMore: hasMoreData } });
      saveState(newAlbums, 1, hasMoreData, 0);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '刷新失败';
      dispatch({ type: 'LOAD_ERROR', payload: errorMessage });
      console.error('刷新图集失败:', err);
    }
  }, [categoryType, categoryId, searchQuery, pwaService, transformAlbum, saveState]);

  // 当分类变化时，从缓存恢复或重新加载
  useEffect(() => {
    const savedState = sessionState.get<{
      albums: AlbumCard[];
      page: number;
      hasMore: boolean;
      scrollPosition: number;
    }>(stateKey);

    if (savedState && savedState.albums.length > 0) {
      // 批量恢复缓存数据
      dispatch({
        type: 'RESTORE_CACHE',
        payload: savedState,
      });
      return;
    }

    // 无缓存，重新加载
    const loadInitialData = async () => {
      dispatch({ type: 'START_LOADING' });
      try {
        const response = await fetchData(1);
        const newAlbums = response.items.map(transformAlbum);
        const hasMoreData = response.page * response.size < response.total;
        dispatch({ type: 'LOAD_SUCCESS', payload: { albums: newAlbums, page: 1, hasMore: hasMoreData } });
        saveState(newAlbums, 1, hasMoreData, 0);
      } catch (err) {
        dispatch({ type: 'LOAD_ERROR', payload: err instanceof Error ? err.message : '加载失败' });
      }
    };
    loadInitialData();
  }, [stateKey, fetchData, transformAlbum, saveState]);

  return {
    albums: state.albums,
    loading: state.loading,
    error: state.error,
    page: state.page,
    hasMore: state.hasMore,
    isLoadingMore: state.isLoadingMore,
    loadMore,
    refresh,
    scrollPosition: state.scrollPosition,
    saveScrollPosition,
  };
};
