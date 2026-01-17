import { apiClient } from './apiInterceptor';

// 导出类
export class PWAService {
  constructor() {
    // 移除了缓存管理器依赖
  }

  async getAlbumDetail(albumId: string): Promise<any> {
    return apiClient.get(`/albums/${albumId}`);
  }

  async refreshAlbumDetail(albumId: string): Promise<any> {
    return apiClient.get(`/albums/${albumId}`);
  }

  async getAlbumImages(albumId: string, page: number = 1, size: number = 20): Promise<any> {
    return apiClient.get(`/albums/${albumId}/images`, { page: page.toString(), size: size.toString() });
  }

  async refreshAlbumImages(albumId: string, page: number = 1, size: number = 20): Promise<any> {
    return apiClient.get(`/albums/${albumId}/images`, { page: page.toString(), size: size.toString() });
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
        endpoint = `/albums/org/${categoryId}`;
        break;
      case 'model':
        endpoint = `/albums/model/${categoryId}`;
        break;
      case 'tag':
        endpoint = `/albums/tag/${categoryId}`;
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
        endpoint = `/albums/org/${categoryId}`;
        break;
      case 'model':
        endpoint = `/albums/model/${categoryId}`;
        break;
      case 'tag':
        endpoint = `/albums/tag/${categoryId}`;
        break;
      default:
        throw new Error(`不支持的分类类型: ${categoryType}`);
    }

    return apiClient.get(endpoint, { page: page.toString(), size: size.toString() });
  }

  async getAlbums(page: number = 1, size: number = 20): Promise<any> {
    return apiClient.get('/albums/', { page: page.toString(), size: size.toString() });
  }

  async refreshAlbums(page: number = 1, size: number = 20): Promise<any> {
    return apiClient.get('/albums/', { page: page.toString(), size: size.toString() });
  }

  async searchAlbums(query: string, page: number = 1, size: number = 20): Promise<any> {
    return apiClient.get('/albums/', { page: page.toString(), size: size.toString(), search: query });
  }

  async getCategoryTree(): Promise<any> {
    return apiClient.get('/categories/');
  }

  async refreshCategoryTree(): Promise<any> {
    return apiClient.get('/categories/');
  }
}
