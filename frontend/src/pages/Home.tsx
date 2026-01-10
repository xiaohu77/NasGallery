import { Link, useParams, useLocation, useNavigate } from 'react-router-dom'
import { useState, useEffect, useCallback, useRef } from 'react'
import { PWAService } from '../services/pwaService'
import { AlbumSummary, AlbumCard } from '../types/album'
import { useAlbums } from '../hooks/useAlbums'

const API_BASE = import.meta.env.VITE_API_BASE || 'https://back.xiaohu777.cn'

const SkeletonCard = (): JSX.Element => (
  <div className="card animate-pulse">
    <div className="relative overflow-hidden aspect-[2/3] bg-gray-200 dark:bg-gray-800">
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-gray-300 dark:border-gray-700 border-t-transparent rounded-full animate-spin"></div>
      </div>
    </div>
    <div className="p-4 space-y-2">
      <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-3/4"></div>
      <div className="h-3 bg-gray-200 dark:bg-gray-800 rounded w-full"></div>
      <div className="h-3 bg-gray-200 dark:bg-gray-800 rounded w-5/6"></div>
    </div>
  </div>
)

const Home = (): JSX.Element => {
  const { id } = useParams<{ id?: string }>()
  const location = useLocation()
  const navigate = useNavigate()
  const mainRef = useRef<HTMLDivElement>(null)
  
  const [pwaService] = useState(() => new PWAService())
  
  // 解析当前路由信息
  const currentCategory = useCallback(() => {
    const path = location.pathname
    
    // 首页（全部图集）
    if (path === '/') {
      return { type: null, id: null, name: null }
    }
    
    // 解析路由：/org/123, /model/456, /tag/789
    const segments = path.split('/')
    if (segments.length >= 3) {
      const type = segments[1] as 'org' | 'model' | 'tag'
      const categoryId = parseInt(segments[2])
      
      // 根据类型获取分类名称（可选，用于显示）
      let name: string | null = null
      if (type === 'org') name = '套图'
      if (type === 'model') name = '模特'
      if (type === 'tag') name = '标签'
      
      return { type, id: categoryId, name }
    }
    
    return { type: null, id: null, name: null }
  }, [location.pathname])

  const cat = currentCategory()
  
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
  } = useAlbums(cat.type, cat.id, pwaService)

  // 懒加载观察器
  const observerRef = useRef<IntersectionObserver | null>(null)
  const loadMoreRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!hasMore || isLoadingMore) return

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !isLoadingMore) {
          loadMore()
        }
      },
      { threshold: 0.1, rootMargin: '100px' }
    )

    observerRef.current = observer

    if (loadMoreRef.current) {
      observer.observe(loadMoreRef.current)
    }

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect()
        observerRef.current = null
      }
    }
  }, [hasMore, isLoadingMore, loadMore])

  // 滚动位置保存和恢复 - 只在组件挂载时恢复一次
  const hasRestoredScroll = useRef(false)
  useEffect(() => {
    if (scrollPosition > 0 && mainRef.current && !hasRestoredScroll.current) {
      // 使用 setTimeout 确保 DOM 已经渲染完成
      setTimeout(() => {
        if (mainRef.current) {
          mainRef.current.scrollTo({ top: scrollPosition, behavior: 'auto' });
          hasRestoredScroll.current = true;
        }
      }, 50);
    }
  }, [scrollPosition, loading]);

  // 重试加载
  const handleRetry = () => {
    refresh()
  }

  // 获取当前分类显示名称
  const getCategoryDisplayName = useCallback(() => {
    const cat = currentCategory()
    if (!cat.type) return '全部图集'
    
    const typeNames = {
      org: '套图',
      model: '模特',
      tag: '标签'
    }
    return `${typeNames[cat.type]} - ${cat.name || cat.id}`
  }, [currentCategory])

  return (
    <div className="py-4 px-4 sm:px-6 lg:px-8 hide-scrollbar" ref={mainRef} onScroll={(e) => {
      const target = e.currentTarget;
      saveScrollPosition(target.scrollTop);
    }}>
      {/* 分类标题 */}
      <div className="mb-4">
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
          {getCategoryDisplayName()}
        </h2>
      </div>

      {/* 错误提示 */}
      {error && (!albums || albums.length === 0) && (
        <div className="text-center py-8">
          <div className="text-red-600 dark:text-red-400 mb-4">加载失败: {error}</div>
          <button
            onClick={handleRetry}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            重试
          </button>
        </div>
      )}

      {/* 图集网格 */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-3 xl:grid-cols-4 gap-3">
        {loading && (!albums || albums.length === 0) ? (
          // 初始加载骨架屏
          Array.from({ length: 8 }).map((_, index) => (
            <SkeletonCard key={index} />
          ))
        ) : (
          <>
            {albums && albums.map((album) => (
              <Link
                key={album.id}
                to={`/album/${album.id}`}
                className="card group flex flex-col"
                onClick={(e) => {
                  // 阻止默认行为，使用编程式导航以便更好地控制
                  e.preventDefault();
                  navigate(`/album/${album.id}`);
                }}
              >
                <div className="relative overflow-hidden aspect-[2/3] flex-shrink-0">
                  {album.coverImage ? (
                    <img
                      src={album.coverImage}
                      alt={album.title}
                      className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                      loading="lazy"
                      onError={(e) => {
                        const target = e.target as HTMLImageElement
                        target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="300"%3E%3Crect width="400" height="300" fill="%23e0e0e0"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dy=".3em" fill="%23999"%3E无封面%3C/text%3E%3C/svg%3E'
                      }}
                    />
                  ) : (
                    <div className="w-full h-full bg-gray-200 dark:bg-gray-800 flex items-center justify-center">
                      <span className="text-gray-400 text-sm">无封面</span>
                    </div>
                  )}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  <div className="absolute bottom-0 left-0 right-0 p-2 text-white opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                    <span className="text-xs font-medium bg-white/20 px-1.5 py-0.5 rounded backdrop-blur-sm">
                      {album.imageCount} 张
                    </span>
                  </div>
                </div>
                <div className="p-2">
                  <h3
                    className="text-sm font-semibold mb-1 text-slate-900 dark:text-white group-hover:text-slate-600 dark:group-hover:text-slate-300 transition-colors line-clamp-2"
                    title={album.title}
                  >
                    {album.title}
                  </h3>
                  <p
                    className="text-xs text-slate-600 dark:text-slate-400 line-clamp-2"
                    title={album.description}
                  >
                    {album.description}
                  </p>
                </div>
              </Link>
            ))}

            {/* 加载更多指示器 */}
            {hasMore && albums && albums.length > 0 && (
              <div
                ref={loadMoreRef}
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
        )}
      </div>
    </div>
  )
}

export default Home