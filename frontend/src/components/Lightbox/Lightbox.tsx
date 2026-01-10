import { CloseIcon } from '../icons'
import { ImageItem, ZoomState } from '../../types/album'
import LightboxImage from './LightboxImage'
import ThumbnailList from './ThumbnailList'

interface LightboxProps {
  isOpen: boolean
  selectedImage: ImageItem | null
  images: ImageItem[]
  zoom: ZoomState
  isDragging: boolean
  onClose: () => void
  onPrev: () => void
  onNext: () => void
  onThumbnailClick: (image: ImageItem) => void
  onWheel: (e: React.WheelEvent) => void
  onMouseDown: (e: React.MouseEvent) => void
  onMouseMove: (e: React.MouseEvent) => void
  onMouseUp: () => void
  onMouseLeave: () => void
  onTouchStart: (e: React.TouchEvent) => void
  onTouchMove: (e: React.TouchEvent) => void
  onTouchEnd: (e: React.TouchEvent) => void
}

const Lightbox = ({
  isOpen,
  selectedImage,
  images,
  zoom,
  isDragging,
  onClose,
  onThumbnailClick,
  onWheel,
  onMouseDown,
  onMouseMove,
  onMouseUp,
  onMouseLeave,
  onTouchStart,
  onTouchMove,
  onTouchEnd
}: LightboxProps) => {
  if (!isOpen || !selectedImage) return null

  const currentIndex = images.findIndex(img => img.id === selectedImage.id)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm p-4 lightbox-container">
      <div className="relative max-w-6xl w-full max-h-[90vh] flex flex-col hide-scrollbar">
        {/* 头部 */}
        <div className="flex items-center justify-between mb-4">
          <div className="text-white">
            <h3 className="text-lg font-semibold">{selectedImage.title}</h3>
            <p className="text-sm text-gray-300">{selectedImage.description}</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="btn btn-ghost p-2 rounded-lg text-white hover:bg-white/10"
              aria-label="关闭"
            >
              <CloseIcon className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* 图片区域 */}
        <LightboxImage
          imageUrl={selectedImage.url}
          title={selectedImage.title}
          zoom={zoom}
          onWheel={onWheel}
          onMouseDown={onMouseDown}
          onMouseMove={onMouseMove}
          onMouseUp={onMouseUp}
          onMouseLeave={onMouseLeave}
          onTouchStart={onTouchStart}
          onTouchMove={onTouchMove}
          onTouchEnd={onTouchEnd}
          isDragging={isDragging}
        />

        {/* 进度指示 */}
        <div className="mt-4 text-center text-white text-sm">
          <span className="bg-white/10 px-3 py-1 rounded">
            {currentIndex + 1} / {images.length}
          </span>
          {zoom.level > 1 && (
            <span className="ml-2 bg-white/10 px-2 py-1 rounded text-xs">
              放大: {Math.round(zoom.level * 100)}%
            </span>
          )}
        </div>

        {/* 预览图列表 */}
        <ThumbnailList
          images={images}
          selectedImage={selectedImage}
          onThumbnailClick={onThumbnailClick}
        />
      </div>
    </div>
  )
}

export default Lightbox