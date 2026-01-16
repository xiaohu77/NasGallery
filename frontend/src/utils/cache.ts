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
  // 状态键
  state: {
    albums: (type: string | null, id: number | null) => `state:albums:${type || 'all'}:${id || 'all'}`,
    albumDetail: (id: string) => `state:album:${id}`
  }
};

// 导出单例实例
export const sessionState = SessionState.getInstance();