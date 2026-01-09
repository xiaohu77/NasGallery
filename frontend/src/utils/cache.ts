/**
 * 数据缓存管理器
 * 支持内存缓存和会话缓存，用于减少重复请求
 */

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  expiry: number;
}

class DataCache {
  private static instance: DataCache;
  private memoryCache: Map<string, CacheEntry<any>> = new Map();
  private readonly DEFAULT_TTL = 5 * 60 * 1000; // 5分钟默认过期时间
  private readonly MAX_MEMORY_SIZE = 50; // 最大缓存条目数

  private constructor() {}

  static getInstance(): DataCache {
    if (!DataCache.instance) {
      DataCache.instance = new DataCache();
    }
    return DataCache.instance;
  }

  /**
   * 设置缓存
   */
  set<T>(key: string, data: T, ttl?: number): void {
    const expiry = ttl || this.DEFAULT_TTL;
    const entry: CacheEntry<T> = {
      data,
      timestamp: Date.now(),
      expiry
    };

    // 清理过期条目
    this.cleanup();

    // 如果缓存已满，移除最旧的条目
    if (this.memoryCache.size >= this.MAX_MEMORY_SIZE) {
      const oldestKey = this.findOldestKey();
      if (oldestKey) {
        this.memoryCache.delete(oldestKey);
      }
    }

    this.memoryCache.set(key, entry);
    
    // 设置自动清理
    setTimeout(() => {
      const cached = this.memoryCache.get(key);
      if (cached && this.isExpired(cached)) {
        this.memoryCache.delete(key);
      }
    }, expiry + 1000);
  }

  /**
   * 获取缓存
   */
  get<T>(key: string): T | null {
    const entry = this.memoryCache.get(key);
    
    if (!entry) {
      return null;
    }

    if (this.isExpired(entry)) {
      this.memoryCache.delete(key);
      return null;
    }

    return entry.data;
  }

  /**
   * 检查缓存是否存在且未过期
   */
  has(key: string): boolean {
    const entry = this.memoryCache.get(key);
    if (!entry) return false;
    
    if (this.isExpired(entry)) {
      this.memoryCache.delete(key);
      return false;
    }
    
    return true;
  }

  /**
   * 删除缓存
   */
  delete(key: string): void {
    this.memoryCache.delete(key);
  }

  /**
   * 清空所有缓存
   */
  clear(): void {
    this.memoryCache.clear();
  }

  /**
   * 清理过期缓存
   */
  private cleanup(): void {
    const now = Date.now();
    for (const [key, entry] of this.memoryCache.entries()) {
      if (now - entry.timestamp > entry.expiry) {
        this.memoryCache.delete(key);
      }
    }
  }

  /**
   * 检查条目是否过期
   */
  private isExpired(entry: CacheEntry<any>): boolean {
    return Date.now() - entry.timestamp > entry.expiry;
  }

  /**
   * 找到最旧的缓存键
   */
  private findOldestKey(): string | null {
    let oldestKey: string | null = null;
    let oldestTimestamp = Infinity;

    for (const [key, entry] of this.memoryCache.entries()) {
      if (entry.timestamp < oldestTimestamp) {
        oldestTimestamp = entry.timestamp;
        oldestKey = key;
      }
    }

    return oldestKey;
  }

  /**
   * 获取缓存统计信息
   */
  getStats(): { size: number; keys: string[] } {
    return {
      size: this.memoryCache.size,
      keys: Array.from(this.memoryCache.keys())
    };
  }
}

/**
 * 会话状态管理器
 * 用于保存页面状态（如滚动位置、当前页码等）
 */
class SessionState {
  private static instance: SessionState;
  private states: Map<string, any> = new Map();

  private constructor() {}

  static getInstance(): SessionState {
    if (!SessionState.instance) {
      SessionState.instance = new SessionState();
    }
    return SessionState.instance;
  }

  /**
   * 保存状态
   */
  set<T>(key: string, state: T): void {
    this.states.set(key, state);
  }

  /**
   * 获取状态
   */
  get<T>(key: string): T | null {
    return this.states.get(key) || null;
  }

  /**
   * 删除状态
   */
  delete(key: string): void {
    this.states.delete(key);
  }

  /**
   * 清空所有状态
   */
  clear(): void {
    this.states.clear();
  }

  /**
   * 检查状态是否存在
   */
  has(key: string): boolean {
    return this.states.has(key);
  }
}

/**
 * 缓存键生成器
 */
export const CacheKeys = {
  // 列表缓存
  albums: (type: string | null, id: number | null, page: number) => 
    `albums:${type || 'all'}:${id || 'all'}:${page}`,
  
  // 详情缓存
  albumDetail: (id: string) => `album:detail:${id}`,
  
  // 图片列表缓存
  albumImages: (id: string, page: number) => `album:images:${id}:${page}`,
  
  // 分类缓存
  categories: 'categories:tree',
  
  // 状态键
  state: {
    albums: (type: string | null, id: number | null) => `state:albums:${type || 'all'}:${id || 'all'}`,
    albumDetail: (id: string) => `state:album:${id}`
  }
};

// 导出单例实例
export const dataCache = DataCache.getInstance();
export const sessionState = SessionState.getInstance();

/**
 * 包装异步函数，添加缓存支持
 */
export async function withCache<T>(
  key: string,
  fetchFn: () => Promise<T>,
  ttl?: number
): Promise<T> {
  // 检查缓存
  const cached = dataCache.get<T>(key);
  if (cached !== null) {
    return cached;
  }

  // 执行请求
  const data = await fetchFn();
  
  // 存入缓存
  dataCache.set(key, data, ttl);
  
  return data;
}

/**
 * 清除相关缓存
 */
export function invalidateRelatedCache(pattern: string): void {
  const stats = dataCache.getStats();
  const regex = new RegExp(pattern);
  
  stats.keys.forEach(key => {
    if (regex.test(key)) {
      dataCache.delete(key);
    }
  });
}