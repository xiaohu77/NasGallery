const API_BASE = import.meta.env.VITE_API_BASE || 'https://back.xiaohu777.cn';

// 导出类
export class PWAService {
  constructor() {
    // 移除了缓存管理器依赖
  }

  async getAlbumDetail(albumId: string): Promise<any> {
    const response = await fetch(`${API_BASE}/albums/${albumId}`);
    const data = await response.json();
    return data;
  }

  async refreshAlbumDetail(albumId: string): Promise<any> {
    const response = await fetch(`${API_BASE}/albums/${albumId}`);
    const data = await response.json();
    return data;
  }

  async getAlbumImages(albumId: string, page: number = 1, size: number = 20): Promise<any> {
    const response = await fetch(`${API_BASE}/albums/${albumId}/images?page=${page}&size=${size}`);
    const data = await response.json();
    return data;
  }

  async refreshAlbumImages(albumId: string, page: number = 1, size: number = 20): Promise<any> {
    const response = await fetch(`${API_BASE}/albums/${albumId}/images?page=${page}&size=${size}`);
    const data = await response.json();
    return data;
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
        endpoint = `${API_BASE}/albums/org/${categoryId}`;
        break;
      case 'model':
        endpoint = `${API_BASE}/albums/model/${categoryId}`;
        break;
      case 'tag':
        endpoint = `${API_BASE}/albums/tag/${categoryId}`;
        break;
      default:
        throw new Error(`不支持的分类类型: ${categoryType}`);
    }

    const response = await fetch(`${endpoint}?page=${page}&size=${size}`);
    const data = await response.json();
    return data;
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
        endpoint = `${API_BASE}/albums/org/${categoryId}`;
        break;
      case 'model':
        endpoint = `${API_BASE}/albums/model/${categoryId}`;
        break;
      case 'tag':
        endpoint = `${API_BASE}/albums/tag/${categoryId}`;
        break;
      default:
        throw new Error(`不支持的分类类型: ${categoryType}`);
    }

    const response = await fetch(`${endpoint}?page=${page}&size=${size}`);
    const data = await response.json();
    return data;
  }

  async getAlbums(page: number = 1, size: number = 20): Promise<any> {
    const response = await fetch(`${API_BASE}/albums/?page=${page}&size=${size}`);
    const data = await response.json();
    return data;
  }

  async refreshAlbums(page: number = 1, size: number = 20): Promise<any> {
    const response = await fetch(`${API_BASE}/albums/?page=${page}&size=${size}`);
    const data = await response.json();
    return data;
  }

  async getCategoryTree(): Promise<any> {
    const response = await fetch(`${API_BASE}/categories/`);
    const data = await response.json();
    return data;
  }

  async refreshCategoryTree(): Promise<any> {
    const response = await fetch(`${API_BASE}/categories/`);
    const data = await response.json();
    return data;
  }
}