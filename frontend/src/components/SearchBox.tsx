import { useState, useCallback, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'

interface SearchBoxProps {
  onSearch?: (query: string) => void
  placeholder?: string
  className?: string
}

const SearchBox = ({ onSearch, placeholder = '搜索...', className = '' }: SearchBoxProps) => {
  const navigate = useNavigate()
  const location = useLocation()
  const [query, setQuery] = useState('')

  // 从URL参数初始化搜索词
  useEffect(() => {
    const params = new URLSearchParams(location.search)
    const searchParam = params.get('search')
    if (searchParam) {
      setQuery(searchParam)
    }
  }, [location.search])

  const handleSearch = useCallback((e: React.FormEvent) => {
    e.preventDefault()
    
    if (onSearch) {
      onSearch(query)
    } else {
      // 默认行为：更新URL并触发搜索
      const params = new URLSearchParams(location.search)
      if (query) {
        params.set('search', query)
      } else {
        params.delete('search')
      }
      navigate(`${location.pathname}?${params.toString()}`, { replace: true })
    }
  }, [query, onSearch, navigate, location])

  const handleClear = useCallback(() => {
    setQuery('')
    if (onSearch) {
      onSearch('')
    } else {
      const params = new URLSearchParams(location.search)
      params.delete('search')
      navigate(`${location.pathname}?${params.toString()}`, { replace: true })
    }
  }, [onSearch, navigate, location])

  return (
    <form onSubmit={handleSearch} className={`relative flex items-center ${className}`}>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={placeholder}
        className="w-full px-3 py-1.5 pl-8 pr-8 bg-white/80 dark:bg-black/80 border border-gray-200 dark:border-gray-700 rounded-full text-sm text-slate-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
      />
      <svg
        className="absolute left-2.5 w-3.5 h-3.5 text-gray-400"
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
      {query && (
        <button
          type="button"
          onClick={handleClear}
          className="absolute right-2.5 p-0.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          aria-label="清除搜索"
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
    </form>
  )
}

export default SearchBox
