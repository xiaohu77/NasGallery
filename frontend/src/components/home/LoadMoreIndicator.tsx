import { JSX, forwardRef } from 'react'

interface LoadMoreIndicatorProps {
  loading: boolean
  hasMore: boolean
  onLoadMore?: () => void
}

/**
 * 加载更多指示器组件
 * 用于无限滚动加载
 */
export const LoadMoreIndicator = forwardRef<HTMLDivElement, LoadMoreIndicatorProps>(
  ({ loading, hasMore, onLoadMore }, ref): JSX.Element => {
    if (!hasMore) {
      return (
        <div className="col-span-full text-center py-4 text-sm text-slate-400">
          已加载全部图集
        </div>
      )
    }

    return (
      <div
        ref={ref}
        className="load-more-trigger col-span-full flex justify-center py-4"
      >
        {loading ? (
          <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
            <div className="w-4 h-4 border-2 border-slate-300 dark:border-slate-700 border-t-transparent rounded-full animate-spin"></div>
            <span className="text-sm">加载中...</span>
          </div>
        ) : (
          <button
            onClick={onLoadMore}
            className="text-sm text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
          >
            下滑加载更多...
          </button>
        )}
      </div>
    )
  }
)

LoadMoreIndicator.displayName = 'LoadMoreIndicator'
