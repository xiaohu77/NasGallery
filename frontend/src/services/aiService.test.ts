/**
 * AIService 测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { aiService } from './aiService'

// Mock fetch
const mockFetch = vi.fn()
global.fetch = mockFetch

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  clear: vi.fn()
}
Object.defineProperty(window, 'localStorage', { value: localStorageMock })

describe('AIService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getStatus', () => {
    it('should fetch AI status', async () => {
      const mockStatus = {
        available: true,
        model_info: { loaded: true },
        stats: { total_albums: 100 }
      }
      
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockStatus)
      })
      
      const result = await aiService.getStatus()
      
      expect(mockFetch).toHaveBeenCalledWith('/api/ai/status')
      expect(result).toEqual(mockStatus)
    })

    it('should throw error on failed request', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500
      })
      
      await expect(aiService.getStatus()).rejects.toThrow('HTTP 500')
    })
  })

  describe('startScan', () => {
    it('should start AI scan with GPU', async () => {
      const mockResponse = { success: true, task_id: '123' }
      
      localStorageMock.getItem.mockReturnValue('test-token')
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse)
      })
      
      const result = await aiService.startScan(true)
      
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/ai/scan?use_gpu=true',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token'
          })
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('should start AI scan without GPU', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ success: true })
      })
      
      localStorageMock.getItem.mockReturnValue(null)
      
      await aiService.startScan(false)
      
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/ai/scan?use_gpu=false',
        expect.any(Object)
      )
    })
  })

  describe('search', () => {
    it('should search with query', async () => {
      const mockResponse = {
        query: 'test',
        results: [{ album_id: 1, title: 'Test', similarity: 0.9 }],
        total: 1,
        page: 1,
        size: 20,
        has_more: false
      }
      
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse)
      })
      
      const result = await aiService.search('test')
      
      expect(mockFetch).toHaveBeenCalledWith('/api/ai/search?q=test&limit=20&page=1')
      expect(result).toEqual(mockResponse)
    })

    it('should search with custom pagination', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ results: [] })
      })
      
      await aiService.search('test', 10, 2)
      
      expect(mockFetch).toHaveBeenCalledWith('/api/ai/search?q=test&limit=10&page=2')
    })

    it('should encode query string', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ results: [] })
      })
      
      await aiService.search('test query with spaces')
      
      expect(mockFetch).toHaveBeenCalledWith('/api/ai/search?q=test%20query%20with%20spaces&limit=20&page=1')
    })

    it('should throw error with detail message', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 400,
        json: () => Promise.resolve({ detail: 'Invalid query' })
      })
      
      await expect(aiService.search('')).rejects.toThrow('Invalid query')
    })
  })

  describe('getProviders', () => {
    it('should fetch available providers', async () => {
      const mockProviders = {
        available: ['CPUExecutionProvider'],
        gpu_providers: [],
        cpu_available: true
      }
      
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockProviders)
      })
      
      const result = await aiService.getProviders()
      
      expect(mockFetch).toHaveBeenCalledWith('/api/ai/providers')
      expect(result).toEqual(mockProviders)
    })
  })

  describe('loadModel', () => {
    it('should load model with GPU', async () => {
      const mockResponse = {
        success: true,
        model_info: { loaded: true }
      }
      
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse)
      })
      
      const result = await aiService.loadModel(true)
      
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/ai/model/load?use_gpu=true',
        expect.objectContaining({ method: 'POST' })
      )
      expect(result).toEqual(mockResponse)
    })

    it('should load model with specific provider', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ success: true })
      })
      
      await aiService.loadModel(true, 'CUDAExecutionProvider')
      
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/ai/model/load?use_gpu=true&provider=CUDAExecutionProvider',
        expect.any(Object)
      )
    })
  })
})
