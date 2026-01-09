import { useEffect, useRef } from 'react'
import { ImageItem } from '../../types/album'

interface ThumbnailListProps {
  images: ImageItem[]
  selectedImage: ImageItem | null
  onThumbnailClick: (image: ImageItem) => void
}

const ThumbnailList = ({ images, selectedImage, onThumbnailClick }: ThumbnailListProps) => {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (containerRef.current && selectedImage) {
      const selectedIndex = images.findIndex(img => img.id === selectedImage.id)
      if (selectedIndex >= 0) {
        // 计算滚动位置，使当前图片居中
        const containerWidth = containerRef.current.offsetWidth
        const thumbnailWidth = 64 // w-16 = 64px
        const gap = 8 // gap-2 = 8px
        const itemWidth = thumbnailWidth + gap
        
        // 计算目标滚动位置：使选中项居中
        const targetScroll = selectedIndex * itemWidth - (containerWidth / 2) + (thumbnailWidth / 2)
        
        containerRef.current.scrollTo({
          left: targetScroll,
          behavior: 'smooth'
        })
      }
    }
  }, [selectedImage, images])

  return (
    <div className="mt-4 overflow-x-auto" ref={containerRef}>
      <div className="flex gap-2 pb-2">
        {images.map((image) => {
          const isSelected = image.id === selectedImage?.id
          return (
            <button
              key={image.id}
              onClick={() => onThumbnailClick(image)}
              className={`flex-shrink-0 w-16 h-12 overflow-hidden rounded border-2 transition-all ${
                isSelected
                  ? 'border-white brightness-110'
                  : 'border-transparent opacity-60 hover:opacity-100 hover:border-gray-400'
              }`}
              aria-label={`预览 ${image.title}`}
            >
              <img
                src={image.url}
                alt={image.title}
                className="w-full h-full object-cover"
                loading="lazy"
              />
            </button>
          )
        })}
      </div>
    </div>
  )
}

export default ThumbnailList