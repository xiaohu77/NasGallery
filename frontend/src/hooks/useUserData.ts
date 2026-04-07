import { useState, useEffect, useCallback } from 'react'
import { apiClient } from '../services/apiInterceptor'
import { AlbumCard } from '../types/album'

const API_BASE = import.meta.env.DEV
  ? (import.meta.env.VITE_API_BASE || 'http://localhost:8000')
  : window.location.origin

interface PagedResponse {
  total: number
  page: number
  size: number
  items: any[]
}

interface UseUserDataReturn {
  favorites: AlbumCard[]
  history: AlbumCard[]
  favoritesLoading: boolean
  historyLoading: boolean
  favoritesError: string | null
  historyError: string | null
  hasMoreFavorites: boolean
  hasMoreHistory: boolean
  loadMoreFavorites: () => Promise<void>
  loadMoreHistory: () => Promise<void>
  refreshFavorites: () => Promise<void>
  refreshHistory: () => Promise<void>
  toggleFavorite: (albumId: string) => Promise<boolean>
  isFavorited: (albumId: string) => boolean
  recordView: (albumId: string) => Promise<void>
}

export const useUserData = (): UseUserDataReturn => {
  const [favorites, setFavorites] = useState<AlbumCard[]>([])
  const [history, setHistory] = useState<AlbumCard[]>([])
  const [favoritesPage, setFavoritesPage] = useState(1)
  const [historyPage, setHistoryPage] = useState(1)
  const [favoritesLoading, setFavoritesLoading] = useState(false)
  const [historyLoading, setHistoryLoading] = useState(false)
  const [favoritesError, setFavoritesError] = useState<string | null>(null)
  const [historyError, setHistoryError] = useState<string | null>(null)
  const [favoritesTotal, setFavoritesTotal] = useState(0)
  const [historyTotal, setHistoryTotal] = useState(0)

  const transformAlbum = useCallback((album: any): AlbumCard => {
    let coverImage = album.cover_url || ''
    if (coverImage.startsWith('/')) {
      coverImage = coverImage.startsWith('/covers/')
        ? `${API_BASE}/api${coverImage}`
        : `${API_BASE}${coverImage}`
    }
    return {
      id: album.id.toString(),
      title: album.title,
      description: album.description || '暂无描述',
      coverImage,
      imageCount: album.image_count,
      viewCount: album.view_count,
    }
  }, [])

  const fetchFavorites = useCallback(async (page: number = 1, append: boolean = false) => {
    setFavoritesLoading(true)
    setFavoritesError(null)
    try {
      const response: PagedResponse = await apiClient.get('/api/user/favorites', {
        page: page.toString(),
        size: '20'
      })
      const albums = response.items.map(transformAlbum)
      if (append) {
        setFavorites(prev => [...prev, ...albums])
      } else {
        setFavorites(albums)
      }
      setFavoritesTotal(response.total)
      setFavoritesPage(page)
    } catch (err) {
      setFavoritesError(err instanceof Error ? err.message : '加载收藏失败')
    } finally {
      setFavoritesLoading(false)
    }
  }, [transformAlbum])

  const fetchHistory = useCallback(async (page: number = 1, append: boolean = false) => {
    setHistoryLoading(true)
    setHistoryError(null)
    try {
      const response: PagedResponse = await apiClient.get('/api/user/history', {
        page: page.toString(),
        size: '20'
      })
      const albums = response.items.map(transformAlbum)
      if (append) {
        setHistory(prev => [...prev, ...albums])
      } else {
        setHistory(albums)
      }
      setHistoryTotal(response.total)
      setHistoryPage(page)
    } catch (err) {
      setHistoryError(err instanceof Error ? err.message : '加载历史失败')
    } finally {
      setHistoryLoading(false)
    }
  }, [transformAlbum])

  useEffect(() => {
    fetchFavorites(1)
    fetchHistory(1)
  }, [fetchFavorites, fetchHistory])

  const loadMoreFavorites = useCallback(async () => {
    if (favorites.length >= favoritesTotal || favoritesLoading) return
    await fetchFavorites(favoritesPage + 1, true)
  }, [favorites.length, favoritesTotal, favoritesLoading, favoritesPage, fetchFavorites])

  const loadMoreHistory = useCallback(async () => {
    if (history.length >= historyTotal || historyLoading) return
    await fetchHistory(historyPage + 1, true)
  }, [history.length, historyTotal, historyLoading, historyPage, fetchHistory])

  const refreshFavorites = useCallback(async () => {
    await fetchFavorites(1)
  }, [fetchFavorites])

  const refreshHistory = useCallback(async () => {
    await fetchHistory(1)
  }, [fetchHistory])

  const toggleFavorite = useCallback(async (albumId: string): Promise<boolean> => {
    try {
      const isFav = favorites.some(f => f.id === albumId)
      if (isFav) {
        await apiClient.delete(`/api/user/favorites/${albumId}`)
        setFavorites(prev => prev.filter(f => f.id !== albumId))
        return false
      } else {
        await apiClient.post(`/api/user/favorites/${albumId}`)
        await fetchFavorites(1)
        return true
      }
    } catch (err) {
      console.error('操作收藏失败:', err)
      return isFav
    }
  }, [favorites, fetchFavorites])

  const isFavorited = useCallback((albumId: string): boolean => {
    return favorites.some(f => f.id === albumId)
  }, [favorites])

  const recordView = useCallback(async (albumId: string) => {
    try {
      await apiClient.post(`/api/user/history/${albumId}`)
    } catch (err) {
      console.error('记录浏览失败:', err)
    }
  }, [])

  return {
    favorites,
    history,
    favoritesLoading,
    historyLoading,
    favoritesError,
    historyError,
    hasMoreFavorites: favorites.length < favoritesTotal,
    hasMoreHistory: history.length < historyTotal,
    loadMoreFavorites,
    loadMoreHistory,
    refreshFavorites,
    refreshHistory,
    toggleFavorite,
    isFavorited,
    recordView
  }
}