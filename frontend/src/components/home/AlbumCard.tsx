import { JSX } from 'react'
import { Link } from 'react-router-dom'

const API_BASE = import.meta.env.DEV
  ? (import.meta.env.VITE_API_BASE || 'http://localhost:8000')
  : window.location.origin

interface AlbumCardProps {
  album: {
    id: string
    title: string
    description: string
    coverImage: string
    imageCount: number
  }
  similarity?: number
  index?: number
  onClick?: () => void
}

/**
 * 图集卡片组件
 * 用于展示单个图集的封面和信息
 */
export const AlbumCard = ({ album, similarity, index, onClick }: AlbumCardProps): JSX.Element => {
  const defaultCover = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="300"%3E%3Crect width="400" height="300" fill="%23e0e0e0"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dy=".3em" fill="%23999"%3E无封面%3C/text%3E%3C/svg%3E'

  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const target = e.target as HTMLImageElement
    target.src = defaultCover
  }

  return (
    <Link
      to={`/album/${album.id}`}
      className="group flex flex-col stagger-item"
      style={{ animationDelay: `${(index || 0) * 50}ms` }}
      onClick={(e) => {
        e.preventDefault()
        if (onClick) onClick()
        else window.location.href = `/album/${album.id}`
      }}
    >
      <div className="relative overflow-hidden aspect-[3/4] rounded-2xl bg-gray-100 dark:bg-gray-900">
        {album.coverImage ? (
          <img
            src={album.coverImage}
            alt={album.title}
            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
            loading="lazy"
            onError={handleImageError}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <span className="text-gray-400 text-sm">无封面</span>
          </div>
        )}
        
        {/* 渐变遮罩 */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
        
        {/* 信息标签 */}
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
      
      {/* 标题和描述 */}
      <div className="mt-2 space-y-0.5">
        <h3 className="text-sm font-medium text-gray-900 dark:text-white line-clamp-1">
          {album.title}
        </h3>
        {album.description && (
          <p className="text-xs text-gray-500 dark:text-gray-400 line-clamp-1">
            {album.description}
          </p>
        )}
      </div>
    </Link>
  )
}
