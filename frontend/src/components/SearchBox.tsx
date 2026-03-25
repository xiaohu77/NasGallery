import { useState, useCallback, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'

interface SearchBoxProps {
  onSearch?: (query: string, mode: 'normal' | 'ai') => void
  placeholder?: string
  className?: string
  showModeToggle?: boolean
  aiEnabled?: boolean
}

const SearchBox = ({ 
  onSearch, 
  placeholder = '搜索...', 
  className = '',
  showModeToggle = true,
  aiEnabled = false
}: SearchBoxProps) => {
  const navigate = useNavigate()
  const location = useLocation()
  const [query, setQuery] = useState('')
  const [searchMode, setSearchMode] = useState<'normal' | 'ai'>('normal')

  // 从URL参数初始化搜索词
  useEffect(() => {
    const params = new URLSearchParams(location.search)
    const searchParam = params.get('search')
    const modeParam = params.get('mode')
    if (searchParam) {
      setQuery(searchParam)
    }
    if (modeParam === 'ai') {
      setSearchMode('ai')
    }
  }, [location.search])

  const handleSearch = useCallback((e: React.FormEvent) => {
    e.preventDefault()
    
    if (onSearch) {
      onSearch(query, searchMode)
    } else {
      // 默认行为：更新URL并触发搜索
      const params = new URLSearchParams(location.search)
      if (query) {
        params.set('search', query)
        params.set('mode', searchMode)
      } else {
        params.delete('search')
        params.delete('mode')
      }
      navigate(`${location.pathname}?${params.toString()}`, { replace: true })
    }
  }, [query, searchMode, onSearch, navigate, location])

  const handleClear = useCallback(() => {
    setQuery('')
    if (onSearch) {
      onSearch('', searchMode)
    } else {
      const params = new URLSearchParams(location.search)
      params.delete('search')
      params.delete('mode')
      navigate(`${location.pathname}?${params.toString()}`, { replace: true })
    }
  }, [searchMode, onSearch, navigate, location])

  const toggleMode = useCallback(() => {
    setSearchMode(prev => prev === 'normal' ? 'ai' : 'normal')
  }, [])

  return (
    <form onSubmit={handleSearch} className={`relative flex items-center ${className}`}>
      {/* 搜索图标 */}
      <svg
        className="absolute left-3 w-4 h-4 text-gray-400"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
        />
      </svg>
      
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={searchMode === 'ai' ? 'AI 智能搜索...' : placeholder}
        className={`w-full px-3 py-1.5 pl-9 ${aiEnabled ? 'pr-16' : 'pr-7'} 
          ${searchMode === 'ai' 
            ? 'bg-purple-50/80 dark:bg-purple-900/20 border-purple-300 dark:border-purple-700' 
            : 'bg-white/80 dark:bg-black/80 border-gray-300 dark:border-gray-600'
          } 
          border rounded-full text-sm text-gray-900 dark:text-white placeholder-gray-400 
          focus:outline-none focus:ring-1 transition-all
          ${searchMode === 'ai' 
            ? 'focus:ring-purple-400 focus:border-purple-400' 
            : 'focus:ring-gray-400 focus:border-gray-400'
          }`}
      />
      
      {/* 清除按钮 */}
      {query && (
        <button
          type="button"
          onClick={handleClear}
          className={`${aiEnabled ? 'right-16' : 'right-2'} absolute p-0.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors`}
          aria-label="清除搜索"
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
      
      {/* AI 模式切换按钮 */}
      {showModeToggle && aiEnabled && (
        <button
          type="button"
          onClick={toggleMode}
          className={`absolute right-2 flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium transition-all active:scale-95 ${
            searchMode === 'ai' 
              ? 'bg-purple-500 text-white' 
              : 'bg-gray-500/10 text-gray-500 dark:text-gray-400 hover:bg-gray-500/20'
          }`}
          title={searchMode === 'ai' ? '点击切换普通搜索' : '点击切换 AI 搜索'}
        >
          {searchMode === 'ai' ? (
            <>
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              <span>AI</span>
            </>
          ) : (
            <span>AI</span>
          )}
        </button>
      )}
    </form>
  )
}

export default SearchBox
