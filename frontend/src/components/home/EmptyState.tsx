import { JSX } from 'react'

interface EmptyStateProps {
  title?: string
  description?: string
  icon?: JSX.Element
}

/**
 * 空状态组件
 * 当没有数据时显示
 */
export const EmptyState = ({ 
  title = '暂无数据', 
  description,
  icon 
}: EmptyStateProps): JSX.Element => (
  <div className="flex flex-col items-center justify-center py-16 px-4">
    {icon && (
      <div className="mb-4 text-gray-400">
        {icon}
      </div>
    )}
    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-1">
      {title}
    </h3>
    {description && (
      <p className="text-sm text-gray-500 dark:text-gray-400 text-center max-w-xs">
        {description}
      </p>
    )}
  </div>
)
