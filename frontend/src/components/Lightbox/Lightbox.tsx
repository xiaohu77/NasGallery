import { useState, useEffect, useCallback, useRef } from 'react'
import { ImageItem } from '../../types/album'

interface LightboxProps {
  isOpen: boolean
  images: ImageItem[]
  initialIndex: number
  onClose: () => void
}

// 图片URL处理
const getMediumUrl = (url: string) => {
  const separator = url.includes('?') ? '&' : '?'
  return `${url}${separator}width=1200`
}

const getOriginalUrl = (url: string) => url.split('?')[0]

const Lightbox = ({ isOpen, images, initialIndex, onClose }: LightboxProps) => {
  const [currentIndex, setCurrentIndex] = useState(initialIndex)
  const [offset, setOffset] = useState(0)
  const [transition, setTransition] = useState('')
  const [uiVisible, setUiVisible] = useState(true)
  const [showOriginal, setShowOriginal] = useState(false)
  
  // 缩放、平移、旋转
  const [scale, setScale] = useState(1)
  const [panX, setPanX] = useState(0)
  const [panY, setPanY] = useState(0)
  const [rotation, setRotation] = useState(0)
  
  const gestureRef = useRef({
    startX: 0,
    startY: 0,
    startTime: 0,
    isDragging: false,
    isPanning: false,
    lastTap: 0,
    startDist: 0,
    startAngle: 0,
    startScale: 1,
    startRotation: 0,
    startPanX: 0,
    startPanY: 0,
  })

  useEffect(() => {
    setCurrentIndex(initialIndex)
    resetState()
    setShowOriginal(false)
  }, [initialIndex])

  const resetState = useCallback(() => {
    setOffset(0)
    setScale(1)
    setPanX(0)
    setPanY(0)
    setRotation(0)
  }, [])

  const getDistance = (touches: React.TouchList) => {
    const dx = touches[0].clientX - touches[1].clientX
    const dy = touches[0].clientY - touches[1].clientY
    return Math.sqrt(dx * dx + dy * dy)
  }

  const getAngle = (touches: React.TouchList) => {
    const dx = touches[1].clientX - touches[0].clientX
    const dy = touches[1].clientY - touches[0].clientY
    return Math.atan2(dy, dx) * (180 / Math.PI)
  }

  const goToIndex = useCallback((index: number) => {
    setTransition('transform 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94)')
    setCurrentIndex(index)
    resetState()
    setShowOriginal(false)
    setTimeout(() => setTransition(''), 300)
  }, [resetState])

  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    setTransition('')
    
    if (e.touches.length === 2) {
      const g = gestureRef.current
      g.startDist = getDistance(e.touches)
      g.startAngle = getAngle(e.touches)
      g.startScale = scale
      g.startRotation = rotation
      g.isDragging = false
      g.isPanning = false
    } else if (e.touches.length === 1) {
      const touch = e.touches[0]
      const g = gestureRef.current
      g.startX = touch.clientX
      g.startY = touch.clientY
      g.startTime = Date.now()
      g.startPanX = panX
      g.startPanY = panY
      
      if (scale > 1) {
        g.isPanning = true
        g.isDragging = false
      } else {
        g.isDragging = true
        g.isPanning = false
      }
    }
  }, [scale, rotation, panX, panY])

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    e.preventDefault()
    const g = gestureRef.current

    if (e.touches.length === 2) {
      const currentDist = getDistance(e.touches)
      const currentAngle = getAngle(e.touches)
      
      const newScale = Math.max(0.5, Math.min(4, g.startScale * (currentDist / g.startDist)))
      const newRotation = g.startRotation + (currentAngle - g.startAngle)
      
      setScale(newScale)
      setRotation(newRotation)
      
      if (newScale <= 1) {
        setPanX(0)
        setPanY(0)
      }
    } else if (e.touches.length === 1) {
      const touch = e.touches[0]
      const dx = touch.clientX - g.startX
      const dy = touch.clientY - g.startY

      if (g.isPanning && scale > 1) {
        setPanX(g.startPanX + dx)
        setPanY(g.startPanY + dy)
      } else if (g.isDragging && scale === 1) {
        if (Math.abs(dy) > Math.abs(dx) && dy > 20) {
          const progress = Math.min(1, dy / 300)
          setScale(1 - progress * 0.5)
          setOffset(dy * 0.5)
        } else {
          setOffset(dx)
        }
      }
    }
  }, [scale])

  const handleTouchEnd = useCallback((e: React.TouchEvent) => {
    const g = gestureRef.current
    const screenWidth = window.innerWidth

    if (e.touches.length === 0) {
      if (g.isPanning && scale > 1) {
        // 拖动结束
      } else if (scale < 0.7) {
        onClose()
        return
      } else if (scale > 1) {
        // 放大状态结束
      } else if (g.isDragging) {
        const dx = offset
        const deltaTime = Date.now() - g.startTime
        const velocity = Math.abs(dx) / deltaTime

        if (Math.abs(dx) > screenWidth * 0.25 || velocity > 0.5) {
          if (dx < 0 && currentIndex < images.length - 1) {
            goToIndex(currentIndex + 1)
          } else if (dx > 0 && currentIndex > 0) {
            goToIndex(currentIndex - 1)
          } else {
            setTransition('transform 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94)')
            setOffset(0)
            setTimeout(() => setTransition(''), 300)
          }
        } else {
          setTransition('transform 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94)')
          setOffset(0)
          setScale(1)
          setTimeout(() => setTransition(''), 300)
        }
      }

      g.isDragging = false
      g.isPanning = false
    }
  }, [scale, offset, currentIndex, images.length, goToIndex, onClose])

  const handleClick = useCallback(() => {
    const now = Date.now()
    const isDoubleTap = now - gestureRef.current.lastTap < 300

    if (isDoubleTap) {
      setTransition('transform 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94)')
      setScale(prev => prev > 1 ? 1 : 2)
      setPanX(0)
      setPanY(0)
      setRotation(0)
      setTimeout(() => setTransition(''), 300)
    } else {
      setTimeout(() => {
        if (Date.now() - gestureRef.current.lastTap >= 280) {
          setUiVisible(prev => !prev)
        }
      }, 300)
    }
    gestureRef.current.lastTap = now
  }, [])

  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault()
    setTransition('')
    const delta = e.deltaY > 0 ? -0.15 : 0.15
    setScale(prev => {
      const newScale = Math.max(1, Math.min(4, prev + delta))
      if (newScale === 1) {
        setPanX(0)
        setPanY(0)
        setRotation(0)
      }
      return newScale
    })
  }, [])

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (scale <= 1) return
    e.preventDefault()
    const g = gestureRef.current
    g.startX = e.clientX
    g.startY = e.clientY
    g.startPanX = panX
    g.startPanY = panY
    g.isPanning = true
    setTransition('')
  }, [scale, panX, panY])

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!gestureRef.current.isPanning || scale <= 1 || e.buttons !== 1) return
    const g = gestureRef.current
    setPanX(g.startPanX + (e.clientX - g.startX))
    setPanY(g.startPanY + (e.clientY - g.startY))
  }, [scale])

  const handleMouseUp = useCallback(() => {
    gestureRef.current.isPanning = false
  }, [])

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
      if (e.key === 'ArrowLeft' && currentIndex > 0) goToIndex(currentIndex - 1)
      if (e.key === 'ArrowRight' && currentIndex < images.length - 1) goToIndex(currentIndex + 1)
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [currentIndex, images.length, onClose, goToIndex])

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
      return () => { document.body.style.overflow = '' }
    }
  }, [isOpen])

  if (!isOpen) return null

  const screenWidth = window.innerWidth
  const currentImage = images[currentIndex]

  return (
    <div className="fixed inset-0 z-50 bg-black">
      {/* 图片滑动容器 */}
      <div
        className="absolute inset-0 flex"
        onClick={handleClick}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onWheel={handleWheel}
        style={{
          touchAction: 'none',
          userSelect: 'none',
          transition: transition,
          transform: `translateX(${-currentIndex * screenWidth + offset}px)`,
          cursor: scale > 1 ? 'grab' : 'default',
        }}
      >
        {images.map((image, index) => (
          <div
            key={image.id}
            className="flex-shrink-0 w-screen h-full flex items-center justify-center overflow-hidden"
            style={{
              transition: index === currentIndex ? transition : 'none',
            }}
          >
            <img
              src={index === currentIndex && showOriginal ? getOriginalUrl(image.url) : getMediumUrl(image.url)}
              alt=""
              className="max-w-full max-h-full object-contain select-none pointer-events-none"
              draggable={false}
              style={{
                transition: index === currentIndex ? transition : 'none',
                transform: index === currentIndex 
                  ? `scale(${scale}) translate(${panX / scale}px, ${panY / scale}px) rotate(${rotation}deg)`
                  : 'none',
              }}
            />
          </div>
        ))}
      </div>

      {/* 顶部栏 */}
      <div 
        className={`absolute top-0 left-0 right-0 z-20 flex items-center justify-between px-4 py-3 bg-gradient-to-b from-black/60 to-transparent transition-opacity duration-200 ${uiVisible ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
      >
        <button
          onClick={onClose}
          className="w-10 h-10 flex items-center justify-center text-white"
          aria-label="返回"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" />
          </svg>
        </button>
        
        <div className="flex items-center gap-3">
          <div className="text-white text-sm">
            {currentIndex + 1} / {images.length}
          </div>
          <button
            onClick={() => setShowOriginal(!showOriginal)}
            className={`px-2.5 py-1 text-xs rounded-full transition-colors ${
              showOriginal 
                ? 'bg-white text-black' 
                : 'bg-white/20 text-white/80'
            }`}
          >
            {showOriginal ? '原图' : '原图'}
          </button>
        </div>

        <div className="w-10" />
      </div>

      {/* 底部栏 */}
      <div 
        className={`absolute bottom-0 left-0 right-0 z-20 bg-gradient-to-t from-black/60 to-transparent transition-opacity duration-200 ${uiVisible ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
      >
        {/* 指示器 */}
        <div className="flex items-center justify-center gap-1.5 py-3">
          {images.length <= 20 ? (
            images.map((_, index) => (
              <div
                key={index}
                className={`h-1.5 rounded-full transition-all duration-300 ${
                  index === currentIndex ? 'bg-white w-3' : 'bg-white/40 w-1.5'
                }`}
              />
            ))
          ) : (
            <div className="text-white/60 text-xs">{currentIndex + 1} / {images.length}</div>
          )}
        </div>

        <div className="pb-4" />
      </div>
    </div>
  )
}

export default Lightbox
