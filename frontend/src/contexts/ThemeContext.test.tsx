/**
 * ThemeContext 测试
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { ReactNode } from 'react'
import { ThemeProvider, useTheme } from './ThemeContext'

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  clear: vi.fn()
}
Object.defineProperty(window, 'localStorage', { value: localStorageMock })

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

const wrapper = ({ children }: { children: ReactNode }) => (
  <ThemeProvider>{children}</ThemeProvider>
)

describe('ThemeContext', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    document.documentElement.classList.remove('dark')
  })

  it('should provide default light theme', () => {
    localStorageMock.getItem.mockReturnValue(null)
    
    const { result } = renderHook(() => useTheme(), { wrapper })
    
    expect(result.current.theme).toBe('light')
  })

  it('should load saved theme from localStorage', () => {
    localStorageMock.getItem.mockReturnValue('dark')
    
    const { result } = renderHook(() => useTheme(), { wrapper })
    
    expect(result.current.theme).toBe('dark')
  })

  it('should toggle theme from light to dark', () => {
    localStorageMock.getItem.mockReturnValue('light')
    
    const { result } = renderHook(() => useTheme(), { wrapper })
    
    act(() => {
      result.current.toggleTheme()
    })
    
    expect(result.current.theme).toBe('dark')
  })

  it('should toggle theme from dark to light', () => {
    localStorageMock.getItem.mockReturnValue('dark')
    
    const { result } = renderHook(() => useTheme(), { wrapper })
    
    act(() => {
      result.current.toggleTheme()
    })
    
    expect(result.current.theme).toBe('light')
  })

  it('should save theme to localStorage', () => {
    localStorageMock.getItem.mockReturnValue('light')
    
    const { result } = renderHook(() => useTheme(), { wrapper })
    
    act(() => {
      result.current.toggleTheme()
    })
    
    expect(localStorageMock.setItem).toHaveBeenCalledWith('theme', 'dark')
  })

  it('should add dark class to document when theme is dark', () => {
    localStorageMock.getItem.mockReturnValue('dark')
    
    renderHook(() => useTheme(), { wrapper })
    
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })

  it('should remove dark class from document when theme is light', () => {
    localStorageMock.getItem.mockReturnValue('light')
    
    renderHook(() => useTheme(), { wrapper })
    
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })

  it('should throw error when useTheme is used outside ThemeProvider', () => {
    expect(() => {
      renderHook(() => useTheme())
    }).toThrow('useTheme must be used within ThemeProvider')
  })
})
