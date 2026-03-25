import { ImageItem } from '../../types/album'
import { useState, useEffect, useRef } from 'react'

interface ImageGridProps {
  images: ImageItem[]
  onImageClick: (image: ImageItem) => void
  hasMore?: boolean
  onLoadMore?: () => void
  loading?: boolean
}

// 获取中等图 URL
const getMediumUrl = (url: string) => {
  const separator = url.includes('?') ? '&' : '?'
  return `${url}${separator}width=1200`
}

const ImageGrid = ({ images, onImageClick, hasMore = false, onLoadMore, loading = false }: ImageGridProps) => {
  const [visibleImages, setVisibleImages] = useState<ImageItem[]>([])
  const observerRef = useRef<IntersectionObserver | null>(null)
  const loadMoreRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    setVisibleImages(images)
  }, [images])

  useEffect(() => {
    if (!hasMore || !onLoadMore || loading) return

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loading) {
          onLoadMore()
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
      }
    }
  }, [hasMore, onLoadMore, loading])

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {visibleImages.map((image) => (
        <div
          key={image.id}
          className="card group cursor-pointer overflow-hidden"
          onClick={() => onImageClick(image)}
        >
          <div className="relative overflow-hidden">
            <img
              src={getMediumUrl(image.url)}
              alt={image.title}
              className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
              loading="lazy"
              style={{ aspectRatio: 'auto' }}
            />
            <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors duration-300" />
            <div className="absolute bottom-0 left-0 right-0 p-3 text-white opacity-0 group-hover:opacity-100 transition-opacity duration-300">
              <p className="text-sm font-medium">{image.title}</p>
            </div>
          </div>
        </div>
      ))}

      {hasMore && (
        <div 
          ref={loadMoreRef}
          className="col-span-full flex justify-center py-4"
        >
          {loading ? (
            <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400 text-sm">
              <div className="w-4 h-4 border-2 border-slate-300 dark:border-slate-700 border-t-transparent rounded-full animate-spin"></div>
              <span>加载中...</span>
            </div>
          ) : (
            <span className="text-sm text-slate-400">下滑加载更多...</span>
          )}
        </div>
      )}
    </div>
  )
}

export default ImageGrid
