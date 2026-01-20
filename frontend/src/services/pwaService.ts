import { apiClient } from './apiInterceptor';
import type { ScanResponse, ScanStats, OrphanStats } from '../types/album';

// 导出类
export class PWAService {
  constructor() {
    // 移除了缓存管理器依赖
  }

  async getAlbumDetail(albumId: string): Promise<any> {
    return apiClient.get(`/api/albums/${albumId}`);
  }

  async refreshAlbumDetail(albumId: string): Promise<any> {
    return apiClient.get(`/api/albums/${albumId}`);
  }

  async getAlbumImages(albumId: string, page: number = 1, size: number = 20): Promise<any> {
    return apiClient.get(`/api/albums/${albumId}/images`, { page: page.toString(), size: size.toString() });
  }

  async refreshAlbumImages(albumId: string, page: number = 1, size: number = 20): Promise<any> {
    return apiClient.get(`/api/albums/${albumId}/images`, { page: page.toString(), size: size.toString() });
  }

  async getAlbumsByCategory(
    categoryType: 'org' | 'model' | 'tag',
    categoryId: number,
    page: number = 1,
    size: number = 20
  ): Promise<any> {
    let endpoint: string;
    switch (categoryType) {
      case 'org':
        endpoint = `/api/albums/org/${categoryId}`;
        break;
      case 'model':
        endpoint = `/api/albums/model/${categoryId}`;
        break;
      case 'tag':
        endpoint = `/api/albums/tag/${categoryId}`;
        break;
      default:
        throw new Error(`不支持的分类类型: ${categoryType}`);
    }

    return apiClient.get(endpoint, { page: page.toString(), size: size.toString() });
  }

  async refreshAlbumsByCategory(
    categoryType: 'org' | 'model' | 'tag',
    categoryId: number,
    page: number = 1,
    size: number = 20
  ): Promise<any> {
    let endpoint: string;
    switch (categoryType) {
      case 'org':
        endpoint = `/api/albums/org/${categoryId}`;
        break;
      case 'model':
        endpoint = `/api/albums/model/${categoryId}`;
        break;
      case 'tag':
        endpoint = `/api/albums/tag/${categoryId}`;
        break;
      default:
        throw new Error(`不支持的分类类型: ${categoryType}`);
    }

    return apiClient.get(endpoint, { page: page.toString(), size: size.toString() });
  }

  async getAlbums(page: number = 1, size: number = 20): Promise<any> {
    return apiClient.get('/api/albums/', { page: page.toString(), size: size.toString() });
  }

  async refreshAlbums(page: number = 1, size: number = 20): Promise<any> {
    return apiClient.get('/api/albums/', { page: page.toString(), size: size.toString() });
  }

  async searchAlbums(query: string, page: number = 1, size: number = 20): Promise<any> {
    return apiClient.get('/api/albums/', { page: page.toString(), size: size.toString(), search: query });
  }

  async getCategoryTree(): Promise<any> {
    return apiClient.get('/api/categories/');
  }

  async refreshCategoryTree(): Promise<any> {
    return apiClient.get('/api/categories/');
  }

  // 扫描相关API
  async scanAlbums(fullScan: boolean = false): Promise<ScanResponse> {
    return apiClient.post('/api/scan/', { full_scan: fullScan });
  }

  async scanAlbumsSync(): Promise<ScanResponse> {
    return apiClient.post('/api/scan/sync');
  }

  async getScanStats(): Promise<ScanStats> {
    return apiClient.get('/api/scan/stats');
  }

  async getOrphanStats(): Promise<OrphanStats> {
    return apiClient.get('/api/scan/stats/orphans');
  }

  async cleanupDeletedAlbums(days: number = 30): Promise<{ success: boolean; message: string }> {
    return apiClient.post('/api/scan/cleanup', { days });
  }

  async cleanupOrphans(): Promise<{ success: boolean; message: string }> {
    return apiClient.post('/api/scan/cleanup/orphans');
  }
}
