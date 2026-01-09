import { useState, useEffect, useCallback } from 'react';
import { PWAService } from '../services/pwaService';
import { CategoryTree } from '../types/album';

export const useCategories = (pwaService: PWAService) => {
  const [categories, setCategories] = useState<CategoryTree | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isOffline, setIsOffline] = useState<boolean>(false);

  const loadCategories = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const data = await pwaService.getCategoryTree();
      setCategories(data);
      setIsOffline(false);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '加载分类数据失败';
      setError(errorMessage);
      setIsOffline(!navigator.onLine);
      console.error('加载分类树失败:', err);
    } finally {
      setLoading(false);
    }
  }, [pwaService]);

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const data = await pwaService.refreshCategoryTree();
      setCategories(data);
      setIsOffline(false);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '刷新分类数据失败';
      setError(errorMessage);
      setIsOffline(!navigator.onLine);
      console.error('刷新分类树失败:', err);
    } finally {
      setLoading(false);
    }
  }, [pwaService]);

  useEffect(() => {
    loadCategories();
  }, [loadCategories]);

  return {
    categories,
    loading,
    error,
    refresh,
    isOffline
  };
};