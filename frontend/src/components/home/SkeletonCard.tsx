import { JSX } from 'react'

/**
 * 骨架屏卡片组件
 * 用于加载状态的占位显示
 */
export const SkeletonCard = (): JSX.Element => (
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
