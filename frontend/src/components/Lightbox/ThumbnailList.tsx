import { ImageItem } from '../../types/album'

interface ThumbnailListProps {
  images: ImageItem[]
  selectedImage: ImageItem | null
  onThumbnailClick: (image: ImageItem) => void
}

const ThumbnailList = ({ images, selectedImage, onThumbnailClick }: ThumbnailListProps) => {
  return (
    <div className="mt-4 overflow-x-auto hide-scrollbar">
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