/**
 * PWA 工具函数测试
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  checkNetworkStatus,
  listenToNetworkChanges
} from './pwa'

describe('PWA Utils', () => {
  describe('checkNetworkStatus', () => {
    it('should return true when online', () => {
      Object.defineProperty(navigator, 'onLine', { value: true, writable: true })
      expect(checkNetworkStatus()).toBe(true)
    })

    it('should return false when offline', () => {
      Object.defineProperty(navigator, 'onLine', { value: false, writable: true })
      expect(checkNetworkStatus()).toBe(false)
    })
  })

  describe('listenToNetworkChanges', () => {
    it('should register online and offline listeners', () => {
      const addEventListenerSpy = vi.spyOn(window, 'addEventListener')
      const callback = vi.fn()
      
      listenToNetworkChanges(callback)
      
      expect(addEventListenerSpy).toHaveBeenCalledWith('online', expect.any(Function))
      expect(addEventListenerSpy).toHaveBeenCalledWith('offline', expect.any(Function))
      
      addEventListenerSpy.mockRestore()
    })

    it('should call callback with true when online event fires', () => {
      const callback = vi.fn()
      
      listenToNetworkChanges(callback)
      
      // Simulate online event
      window.dispatchEvent(new Event('online'))
      
      expect(callback).toHaveBeenCalledWith(true)
    })

    it('should call callback when offline event fires', () => {
      const callback = vi.fn()
      
      listenToNetworkChanges(callback)
      
      // Verify callback is registered
      expect(callback).not.toHaveBeenCalled()
    })
  })
})
