import { ZoomState } from '../../types/album'

interface LightboxImageProps {
  imageUrl: string
  title: string
  zoom: ZoomState
  onWheel: (e: React.WheelEvent) => void
  onMouseDown: (e: React.MouseEvent) => void
  onMouseMove: (e: React.MouseEvent) => void
  onMouseUp: () => void
  onMouseLeave: () => void
  onTouchStart: (e: React.TouchEvent) => void
  onTouchMove: (e: React.TouchEvent) => void
  onTouchEnd: (e: React.TouchEvent) => void
  isDragging: boolean
}

const LightboxImage = ({
  imageUrl,
  title,
  zoom,
  onWheel,
  onMouseDown,
  onMouseMove,
  onMouseUp,
  onMouseLeave,
  onTouchStart,
  onTouchMove,
  onTouchEnd,
  isDragging
}: LightboxImageProps) => {
  return (
    <div
      className="flex-1 flex items-center justify-center overflow-hidden rounded-lg"
      onWheel={onWheel}
      onMouseDown={onMouseDown}
      onMouseMove={onMouseMove}
      onMouseUp={onMouseUp}
      onMouseLeave={onMouseLeave}
      onTouchStart={onTouchStart}
      onTouchMove={onTouchMove}
      onTouchEnd={onTouchEnd}
      style={{
        cursor: zoom.level > 1 ? (isDragging ? 'grabbing' : 'grab') : 'default',
        userSelect: 'none',
        touchAction: 'none'
      }}
    >
      <img
        src={imageUrl}
        alt={title}
        className="max-w-full max-h-[70vh] object-contain transition-transform duration-200 ease-out"
        style={{
          aspectRatio: 'auto',
          transform: `scale(${zoom.level}) translate(${zoom.offset.x / zoom.level}px, ${zoom.offset.y / zoom.level}px)`,
          pointerEvents: 'none'
        }}
        draggable={false}
        loading="eager"
      />
    </div>
  )
}

export default LightboxImage