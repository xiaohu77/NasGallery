import { Link, useParams, useLocation, useNavigate } from 'react-router-dom'
import { useState, useEffect, useCallback, useRef } from 'react'
import { PWAService } from '../services/pwaService'
import { useAlbums } from '../hooks/useAlbums'
import { aiService, AISearchResult } from '../services/aiService'

const API_BASE = import.meta.env.DEV
  ? (import.meta.env.VITE_API_BASE || 'http://localhost:8000')
  : window.location.origin

const SkeletonCard = (): JSX.Element => (
  <div className="animate-pulse">
    <div className="relative overflow-hidden aspect-[3/4] rounded-2xl bg-gray-200 dark:bg-gray-800">
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-gray-300 dark:border-gray-600 border-t-transparent rounded-full animate-spin"></div>
      </div>
    </div>
    <div className="mt-2 space-y-1.5">
      <div className="h-3.5 bg-gray-200 dark:bg-gray-800 rounded-lg w-3/4"></div>
      <div className="h-2.5 bg-gray-200 dark:bg-gray-800 rounded-lg w-full"></div>
    </div>
  </div>
)

const Home = (): JSX.Element => {
  const { id } = useParams<{ id?: string }>()
  const location = useLocation()
  const navigate = useNavigate()
  const mainRef = useRef<HTMLDivElement>(null)
  
  const [pwaService] = useState(() => new PWAService())
  const [aiSearchResults, setAiSearchResults] = useState<AISearchResult[]>([])
  const [aiSearchLoading, setAiSearchLoading] = useState(false)
  const [aiSearchError, setAiSearchError] = useState<string | null>(null)
  const [aiSearchHasMore, setAiSearchHasMore] = useState(false)
  const [aiSearchPage, setAiSearchPage] = useState(1)
  const [aiSearchLoadingMore, setAiSearchLoadingMore] = useState(false)
  const [currentAiQuery, setCurrentAiQuery] = useState('')
  
  // 滑动切换分类
  const touchStartX = useRef(0)
  const mainTabs = [
    { path: '/' },
    { path: '/org' },
    { path: '/model' },
    { path: '/cosplayer' },
    { path: '/character' },
  ]
  
  const getCurrentTabIndex = useCallback(() => {
    const path = location.pathname
    if (path.startsWith('/org')) return 1
    if (path.startsWith('/model')) return 2
    if (path.startsWith('/cosplayer')) return 3
    if (path.startsWith('/character')) return 4
    return 0
  }, [location.pathname])
  
  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    touchStartX.current = e.touches[0].clientX
  }, [])
  
  const handleTouchEnd = useCallback((e: React.TouchEvent) => {
    const touchEndX = e.changedTouches[0].clientX
    const diff = touchStartX.current - touchEndX
    const threshold = 80
    
    if (Math.abs(diff) < threshold) return
    
    const currentIndex = getCurrentTabIndex()
    if (diff > 0 && currentIndex < mainTabs.length - 1) {
      navigate(mainTabs[currentIndex + 1].path)
    } else if (diff < 0 && currentIndex > 0) {
      navigate(mainTabs[currentIndex - 1].path)
    }
    
    if (mainRef.current) {
      mainRef.current.scrollTop = 0
    }
  }, [getCurrentTabIndex, navigate])
  
  // 从URL参数获取搜索查询和模式
  const searchQuery = useCallback(() => {
    const params = new URLSearchParams(location.search)
    return params.get('search') || ''
  }, [location.search])
  
  const searchMode = useCallback(() => {
    const params = new URLSearchParams(location.search)
    return params.get('mode') || 'normal'
  }, [location.search])
  
  const query = searchQuery()
  const mode = searchMode()
  
  // 从URL路径提取分类类型和ID
  const getCategoryInfo = useCallback(() => {
    const path = location.pathname
    
    if (path === '/org' || path.startsWith('/org/')) {
      return { type: 'org' as const, categoryId: path.includes('/org/') ? parseInt(id || '0') : null }
    } else if (path === '/model' || path.startsWith('/model/')) {
      return { type: 'model' as const, categoryId: path.includes('/model/') ? parseInt(id || '0') : null }
    } else if (path === '/cosplayer' || path.startsWith('/cosplayer/')) {
      return { type: 'cosplayer' as const, categoryId: path.includes('/cosplayer/') ? parseInt(id || '0') : null }
    } else if (path === '/character' || path.startsWith('/character/')) {
      return { type: 'character' as const, categoryId: path.includes('/character/') ? parseInt(id || '0') : null }
    } else if (path.startsWith('/tag/')) {
      return { type: 'tag' as const, categoryId: parseInt(id || '0') }
    }
    
    return { type: null, categoryId: null }
  }, [location.pathname, id])
  
  const { type: categoryType, categoryId } = getCategoryInfo()
  
  // 使用增强的Hook
  const {
    albums,
    loading,
    error,
    page,
    hasMore,
    isLoadingMore,
    loadMore,
    refresh,
    scrollPosition,
    saveScrollPosition
  } = useAlbums(categoryType, categoryId, pwaService, query)

  // 懒加载观察器
  const observerRef = useRef<IntersectionObserver | null>(null)
  const loadMoreRef = useRef<HTMLDivElement | null>(null)
  
  // 保存滚动位置的回调
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const target = e.currentTarget;
    saveScrollPosition(target.scrollTop);
  }, [saveScrollPosition])

  // 加载更多 AI 搜索结果
  const loadMoreAiResults = useCallback(async () => {
    if (!aiSearchHasMore || aiSearchLoadingMore || !currentAiQuery) return
    
    setAiSearchLoadingMore(true)
    try {
      const nextPage = aiSearchPage + 1
      const response = await aiService.search(currentAiQuery, 20, nextPage)
      setAiSearchResults(prev => [...prev, ...response.results])
      setAiSearchHasMore(response.has_more)
      setAiSearchPage(nextPage)
    } catch (err) {
      console.error('加载更多失败:', err)
    } finally {
      setAiSearchLoadingMore(false)
    }
  }, [aiSearchHasMore, aiSearchLoadingMore, currentAiQuery, aiSearchPage])

  // 判断当前是否是AI搜索模式
  const isAiSearch = mode === 'ai' && query

  // 使用 ref callback 来设置 observer
  const loadMoreRefCallback = useCallback((node: HTMLDivElement | null) => {
    loadMoreRef.current = node
    
    if (!node) return
    
    // 清除旧的 observer
    if (observerRef.current) {
      observerRef.current.disconnect()
    }
    
    const canLoadMore = isAiSearch ? aiSearchHasMore : hasMore
    const isLoading = isAiSearch ? aiSearchLoadingMore : isLoadingMore
    
    if (!canLoadMore || isLoading) return

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          // 重新检查最新的状态
          const currentIsAiSearch = mode === 'ai' && query
          if (currentIsAiSearch) {
            if (aiSearchHasMore && !aiSearchLoadingMore) {
              loadMoreAiResults()
            }
          } else {
            if (hasMore && !isLoadingMore) {
              loadMore()
            }
          }
        }
      },
      { threshold: 0.1, rootMargin: '200px' }
    )

    observerRef.current = observer
    observer.observe(node)
  }, [isAiSearch, hasMore, isLoadingMore, loadMore, aiSearchHasMore, aiSearchLoadingMore, loadMoreAiResults, mode, query])

  // 滚动位置恢复 - 使用 ref 直接恢复，避免状态变化触发重渲染
  const hasRestoredScroll = useRef(false)
  const restoreScrollRef = useCallback((node: HTMLDivElement | null) => {
    if (node && scrollPosition > 0 && !hasRestoredScroll.current) {
      hasRestoredScroll.current = true
      // 使用 requestAnimationFrame 确保 DOM 布局完成
      requestAnimationFrame(() => {
        node.scrollTop = scrollPosition
      })
    }
    mainRef.current = node
  }, [scrollPosition])

  // AI 搜索处理
  useEffect(() => {
    if (mode === 'ai' && query) {
      const performAiSearch = async () => {
        setAiSearchLoading(true)
        setAiSearchError(null)
        setAiSearchResults([])
        setAiSearchPage(1)
        setAiSearchHasMore(false)
        setCurrentAiQuery(query)
        
        try {
          const response = await aiService.search(query, 20, 1)
          setAiSearchResults(response.results)
          setAiSearchHasMore(response.has_more)
          setAiSearchPage(1)
        } catch (err) {
          const errorMessage = err instanceof Error ? err.message : 'AI 搜索失败'
          setAiSearchError(errorMessage)
          console.error('AI 搜索失败:', err)
        } finally {
          setAiSearchLoading(false)
        }
      }
      
      performAiSearch()
    } else {
      setAiSearchResults([])
      setAiSearchError(null)
      setAiSearchHasMore(false)
      setAiSearchPage(1)
      setCurrentAiQuery('')
    }
  }, [mode, query])

  // 重试加载
  const handleRetry = () => {
    if (mode === 'ai') {
      // 重新触发 AI 搜索
      setAiSearchResults([])
      setAiSearchError(null)
    } else {
      refresh()
    }
  }

  // 渲染图集卡片
  const renderAlbumCard = (album: { id: string; title: string; description: string; coverImage: string; imageCount: number }, similarity?: number, index?: number) => (
    <Link
      key={album.id}
      to={`/album/${album.id}`}
      className={`group flex flex-col stagger-item`}
      style={{ animationDelay: `${(index || 0) * 50}ms` }}
      onClick={(e) => {
        e.preventDefault();
        navigate(`/album/${album.id}`);
      }}
    >
      <div className="relative overflow-hidden aspect-[3/4] rounded-2xl bg-gray-100 dark:bg-gray-900">
        {album.coverImage ? (
          <img
            src={album.coverImage}
            alt={album.title}
            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
            loading="lazy"
            onError={(e) => {
              const target = e.target as HTMLImageElement
              target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="300"%3E%3Crect width="400" height="300" fill="%23e0e0e0"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dy=".3em" fill="%23999"%3E无封面%3C/text%3E%3C/svg%3E'
            }}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <span className="text-gray-400 text-sm">无封面</span>
          </div>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
        <div className="absolute bottom-2 left-2 right-2 flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-all duration-300 translate-y-2 group-hover:translate-y-0">
          <span className="text-xs font-medium text-white bg-white/20 backdrop-blur-md px-2 py-1 rounded-full">
            {album.imageCount} 张
          </span>
          {similarity !== undefined && (
            <span className="text-xs font-medium text-white bg-purple-500/80 backdrop-blur-md px-2 py-1 rounded-full">
              {(similarity * 100).toFixed(0)}%
            </span>
          )}
        </div>
      </div>
      <div className="mt-2 px-0.5">
        <h3
          className="text-xs font-medium text-gray-900 dark:text-white line-clamp-2 leading-tight"
          title={album.title}
        >
          {album.title}
        </h3>
      </div>
    </Link>
  )

  return (
    <div className="py-4 px-4 sm:px-6 lg:px-8 hide-scrollbar" ref={restoreScrollRef} onScroll={handleScroll} onTouchStart={handleTouchStart} onTouchEnd={handleTouchEnd}>
      {/* AI 搜索模式提示 */}
      {mode === 'ai' && query && (
        <div className="mb-4 text-center">
          <span className="inline-flex items-center gap-1 text-sm text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/20 px-3 py-1 rounded-full">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            AI 搜索: "{query}"
          </span>
        </div>
      )}

      {/* 错误提示 */}
      {((error && (!albums || albums.length === 0)) || aiSearchError) && (
        <div className="text-center py-8">
          <div className="text-red-600 dark:text-red-400 mb-4">
            加载失败: {error || aiSearchError}
          </div>
          <button
            onClick={handleRetry}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors text-sm"
          >
            重试
          </button>
        </div>
      )}

      {/* 图集网格 */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-3 xl:grid-cols-4 gap-3">
        {/* AI 搜索模式 */}
        {mode === 'ai' && query ? (
          aiSearchLoading ? (
            Array.from({ length: 8 }).map((_, index) => (
              <SkeletonCard key={index} />
            ))
          ) : aiSearchResults.length > 0 ? (
            <>
              {aiSearchResults.map((result, index) => {
                const album = {
                  id: result.album_id.toString(),
                  title: result.title,
                  description: '',
                  coverImage: result.cover_url ? `${API_BASE}/api${result.cover_url}` : '',
                  imageCount: result.image_count || 0
                }
                return renderAlbumCard(album, result.similarity, index)
              })}
              
              {/* 加载更多指示器 */}
              {aiSearchHasMore && (
                <div
                  ref={loadMoreRefCallback}
                  className="load-more-trigger col-span-full flex justify-center py-4"
                >
                  {aiSearchLoadingMore ? (
                    <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
                      <div className="w-4 h-4 border-2 border-slate-300 dark:border-slate-700 border-t-transparent rounded-full animate-spin"></div>
                      <span className="text-sm">加载中...</span>
                    </div>
                  ) : (
                    <span className="text-sm text-slate-400">下滑加载更多...</span>
                  )}
                </div>
              )}
              
              {/* 无更多数据提示 */}
              {!aiSearchHasMore && aiSearchResults.length > 0 && (
                <div className="col-span-full text-center py-4 text-sm text-slate-400">
                  已加载全部图集
                </div>
              )}
            </>
          ) : (
            <div className="col-span-full text-center py-8 text-slate-500">
              没有找到匹配的图集
            </div>
          )
        ) : (
          /* 普通搜索模式 */
          loading && (!albums || albums.length === 0) ? (
            Array.from({ length: 8 }).map((_, index) => (
              <SkeletonCard key={index} />
            ))
          ) : (
            <>
              {albums && albums.map((album, index) => renderAlbumCard(album, undefined, index))}

              {/* 加载更多指示器 */}
              {hasMore && albums && albums.length > 0 && (
                <div
                  ref={loadMoreRefCallback}
                  className="load-more-trigger col-span-full flex justify-center py-4"
                >
                  {isLoadingMore ? (
                    <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
                      <div className="w-4 h-4 border-2 border-slate-300 dark:border-slate-700 border-t-transparent rounded-full animate-spin"></div>
                      <span className="text-sm">加载中...</span>
                    </div>
                  ) : (
                    <span className="text-sm text-slate-400">下滑加载更多...</span>
                  )}
                </div>
              )}

              {/* 无更多数据提示 */}
              {!hasMore && albums && albums.length > 0 && (
                <div className="col-span-full text-center py-4 text-sm text-slate-400">
                  已加载全部图集
                </div>
              )}
            </>
          )
        )}
      </div>
    </div>
  )
}

export default Home