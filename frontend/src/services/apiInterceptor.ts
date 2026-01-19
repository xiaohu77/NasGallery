/**
 * API拦截器
 * 在所有API请求中验证认证令牌
 */

// 动态获取当前域名作为API基础URL
// 在开发环境使用环境变量，生产环境使用当前域名
const API_BASE = import.meta.env.DEV
  ? (import.meta.env.VITE_API_BASE || 'http://localhost:8000')
  : window.location.origin;

/**
 * 获取认证令牌
 */
function getAuthToken(): string | null {
  return localStorage.getItem('auth_token');
}

/**
 * 检查URL是否需要认证
 * @param url 请求URL
 * @returns 是否需要认证
 */
function requiresAuth(url: string): boolean {
  const urlObj = new URL(url);
  
  // 认证相关端点不需要认证
  const authEndpoints = ['/auth/login', '/auth/register'];
  if (authEndpoints.some(endpoint => urlObj.pathname.includes(endpoint))) {
    return false;
  }
  
  // 其他API端点都需要认证
  return urlObj.origin === API_BASE || urlObj.pathname.startsWith('/api');
}

/**
 * 增强的fetch函数，自动添加认证令牌
 * @param input 请求输入
 * @param init 请求初始化选项
 * @returns Promise<Response>
 */
export async function authFetch(
  input: RequestInfo | URL,
  init?: RequestInit
): Promise<Response> {
  const url = typeof input === 'string' ? input : input.toString();
  
  // 检查是否需要认证
  if (requiresAuth(url)) {
    const token = getAuthToken();
    
    if (!token) {
      // 如果没有令牌，抛出认证错误
      throw new Error('未登录，请先登录');
    }
    
    // 克隆请求选项以添加认证头
    const headers = new Headers(init?.headers || {});
    headers.set('Authorization', `Bearer ${token}`);
    
    // 创建新的请求选项
    const newInit: RequestInit = {
      ...init,
      headers,
    };
    
    return fetch(input, newInit);
  }
  
  // 不需要认证的请求直接发送
  return fetch(input, init);
}

/**
 * API客户端类
 * 提供统一的API请求方法
 */
export class ApiClient {
  private baseUrl: string;
  
  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || API_BASE;
  }
  
  /**
   * 发送GET请求
   */
  async get<T>(endpoint: string, params?: Record<string, string>): Promise<T> {
    const url = new URL(endpoint, this.baseUrl);
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        url.searchParams.append(key, value);
      });
    }
    
    const response = await authFetch(url.toString());
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return response.json();
  }
  
  /**
   * 发送POST请求
   */
  async post<T>(endpoint: string, data?: any): Promise<T> {
    const url = new URL(endpoint, this.baseUrl);
    
    const response = await authFetch(url.toString(), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return response.json();
  }
  
  /**
   * 发送PUT请求
   */
  async put<T>(endpoint: string, data?: any): Promise<T> {
    const url = new URL(endpoint, this.baseUrl);
    
    const response = await authFetch(url.toString(), {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return response.json();
  }
  
  /**
   * 发送DELETE请求
   */
  async delete<T>(endpoint: string): Promise<T> {
    const url = new URL(endpoint, this.baseUrl);
    
    const response = await authFetch(url.toString(), {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return response.json();
  }
}

// 导出单例实例
export const apiClient = new ApiClient();
