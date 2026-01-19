import { useState, useEffect } from 'react';
import { Album } from '../types/album';
import { PWAService } from '../services/pwaService';

const API_BASE = import.meta.env.DEV
  ? (import.meta.env.VITE_API_BASE || 'http://localhost:8000')
  : window.location.origin;

export const useAlbumData = (id: string | undefined, pwaService: PWAService) => {
  const [album, setAlbum] = useState<Album | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isOffline, setIsOffline] = useState<boolean>(false);

  useEffect(() => {
    if (!id) {
      setLoading(false);
      return;
    }

    const fetchAlbumData = async () => {
      try {
        setLoading(true);
        setError(null);

        const albumDetail = await pwaService.getAlbumDetail(id);

        const transformedAlbum: Album = {
          id: albumDetail.id.toString(),
          title: albumDetail.title,
          description: albumDetail.description || '暂无描述',
          coverImage: albumDetail.cover_image
            ? `${API_BASE}/albums/${albumDetail.id}/images/${albumDetail.cover_image}`
            : '',
          imageCount: albumDetail.image_count || 0
        };

        setAlbum(transformedAlbum);
        setIsOffline(false);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : '加载失败';
        setError(errorMessage);
        setIsOffline(!navigator.onLine);
        console.error('加载图集数据失败:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAlbumData();
  }, [id, pwaService]);

  const refresh = async () => {
    if (!id) return;

    try {
      setLoading(true);
      setError(null);

      const albumDetail = await pwaService.refreshAlbumDetail(id);

      const transformedAlbum: Album = {
        id: albumDetail.id.toString(),
        title: albumDetail.title,
        description: albumDetail.description || '暂无描述',
        coverImage: albumDetail.cover_image
          ? `${API_BASE}/albums/${albumDetail.id}/images/${albumDetail.cover_image}`
          : '',
        imageCount: albumDetail.image_count || 0
      };

      setAlbum(transformedAlbum);
      setIsOffline(false);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '刷新失败';
      setError(errorMessage);
      setIsOffline(!navigator.onLine);
      console.error('刷新图集数据失败:', err);
    } finally {
      setLoading(false);
    }
  };

  return { album, loading, error, isOffline, refresh };
};