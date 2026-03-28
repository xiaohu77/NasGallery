const API_BASE = import.meta.env.VITE_API_BASE || ''

export interface GPUProvider {
  name: string
  display_name: string
  description: string
}

export interface ProvidersInfo {
  available: string[]
  gpu_providers: GPUProvider[]
  cpu_available: boolean
}

export interface AIStatus {
  available: boolean
  model_info: {
    loaded: boolean
    version: string
    embedding_dim: number
    model_dir: string
    providers: string[]
    current_provider: string | null
    available_providers: ProvidersInfo
  }
  stats: {
    total_albums: number
    embedded_albums: number
    pending_albums: number
    latest_task: ScanTaskStatus | null
    model_info: {
      loaded: boolean
      version: string
      embedding_dim: number
      model_dir: string
      providers: string[]
      current_provider: string | null
      available_providers: ProvidersInfo
    }
  }
}

export interface ScanTaskStatus {
  task_id: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'no_task'
  total: number
  processed: number
  failed: number
  progress: number
  error?: string
  message?: string
  started_at?: string
  completed_at?: string
}

export interface AISearchResult {
  album_id: number
  title: string
  cover_url: string
  image_count: number
  similarity: number
}

export interface AISearchResponse {
  query: string
  results: AISearchResult[]
  total: number
  page: number
  size: number
  has_more: boolean
}

export interface StartScanResponse {
  success: boolean
  message: string
  task_id?: string
}

class AIService {
  private baseUrl: string

  constructor() {
    this.baseUrl = `${API_BASE}/api/ai`
  }

  /**
   * 获取 AI 状态
   */
  async getStatus(): Promise<AIStatus> {
    const response = await fetch(`${this.baseUrl}/status`)
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    return response.json()
  }

  /**
   * 启动 AI 扫描
   */
  async startScan(useGpu: boolean = true): Promise<StartScanResponse> {
    const token = localStorage.getItem('token')
    const response = await fetch(`${this.baseUrl}/scan?use_gpu=${useGpu}`, {
      method: 'POST',
      headers: {
        'Authorization': token ? `Bearer ${token}` : ''
      }
    })
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    return response.json()
  }

  /**
   * 获取扫描任务状态
   */
  async getScanStatus(taskId?: string): Promise<ScanTaskStatus> {
    const url = taskId 
      ? `${this.baseUrl}/scan/status?task_id=${taskId}`
      : `${this.baseUrl}/scan/status`
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    return response.json()
  }

  /**
   * 创建 SSE 连接获取扫描进度
   */
  createScanProgressStream(onProgress: (data: ScanTaskStatus) => void): EventSource {
    const eventSource = new EventSource(`${this.baseUrl}/scan/progress`)
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type !== 'heartbeat') {
          onProgress(data)
        }
      } catch (e) {
        console.error('解析 SSE 数据失败:', e)
      }
    }

    eventSource.onerror = (error) => {
      console.error('SSE 连接错误:', error)
      eventSource.close()
    }

    return eventSource
  }

  /**
   * AI 搜索
   */
  async search(query: string, limit: number = 20, page: number = 1): Promise<AISearchResponse> {
    const response = await fetch(
      `${this.baseUrl}/search?q=${encodeURIComponent(query)}&limit=${limit}&page=${page}`
    )
    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }
    return response.json()
  }

  /**
   * 加载模型
   */
  async loadModel(useGpu: boolean = true, provider?: string): Promise<{ success: boolean; model_info: AIStatus['model_info'] }> {
    const params = new URLSearchParams({ use_gpu: useGpu.toString() })
    if (provider) {
      params.append('provider', provider)
    }
    
    const response = await fetch(`${this.baseUrl}/model/load?${params}`, {
      method: 'POST'
    })
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    return response.json()
  }

  /**
   * 获取可用的执行提供程序
   */
  async getProviders(): Promise<ProvidersInfo> {
    const response = await fetch(`${this.baseUrl}/providers`)
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    return response.json()
  }
}

export const aiService = new AIService()
