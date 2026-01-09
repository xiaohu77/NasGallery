import { useParams, useNavigate } from 'react-router-dom'
import { useCallback, useEffect, useRef, useState } from 'react'

// Hook 导入
import { useAlbumData } from '../hooks/useAlbumData'
import { useLazyImages } from '../hooks/useLazyImages'
import { useImageNavigation } from '../hooks/useImageNavigation'
import { useImageZoom } from '../hooks/useImageZoom'
import { useImageDrag } from '../hooks/useImageDrag'
import { useLightbox } from '../hooks/useLightbox'

// 组件导入
import AlbumHeader from '../components/Album/AlbumHeader'
import ImageGrid from '../components/Album/ImageGrid'
import Lightbox from '../components/Lightbox/Lightbox'

// 服务导入
import { PWAService } from '../services/pwaService'


const AlbumDetail = (): JSX.Element => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [pwaService] = useState(() => new PWAService())
  
  // 数据管理 - 图集详情
  const { album, loading: albumLoading, error: albumError, refresh: refreshAlbum } = useAlbumData(id, pwaService)
  
  // 懒加载图片管理 - 一次最多加载3张
  const {
    images,
    loading: imagesLoading,
    error: imagesError,
    hasMore,
    loadMore,
    refresh: refreshImages,
    total,
    loadedCount
  } = useLazyImages(id, pwaService)
  
  const loading = albumLoading || imagesLoading
  const error = albumError || imagesError

  // 图片导航 - 使用共享的images数据
  const {
    selectedImage,
    setSelectedImage,
    handlePrevImage,
    handleNextImage
  } = useImageNavigation(images, null)
  
  // 缩放管理
  const {
    zoom,
    handleWheel,
    handlePinchZoom,
    resetZoom,
    updateOffset
  } = useImageZoom()
  
  // 拖动管理
  const {
    drag,
    handleMouseDown,
    handleMouseMove,
    handleMouseUp,
    handleTouchDrag
  } = useImageDrag(zoom)
  
  // 灯箱管理 - 使用共享的images数据
  const {
    isOpen,
    setIsOpen,
    touchState,
    handleTouchStart,
    handleTouchMove,
    handleTouchEnd,
    setTouchMoving,
    getTouchDistance
  } = useLightbox(images)

  // 移除预加载逻辑，依赖浏览器HTTP缓存

  // 处理图片点击（打开灯箱）
  const handleImageClick = useCallback((image: any): void => {
    if (zoom.level === 1) {
      setSelectedImage(image)
      setIsOpen(true)
      resetZoom()
    }
  }, [zoom.level, setSelectedImage, setIsOpen, resetZoom])

  // 处理关闭灯箱
  const handleCloseModal = useCallback((): void => {
    setSelectedImage(null)
    setIsOpen(false)
    resetZoom()
  }, [setSelectedImage, setIsOpen, resetZoom])

  // 处理缩放（整合鼠标和触摸）
  const handleWheelCallback = useCallback((e: React.WheelEvent): void => {
    handleWheel(e)
  }, [handleWheel])

  // 处理鼠标拖动
  const handleMouseMoveCallback = useCallback((e: React.MouseEvent): void => {
    const newOffset = handleMouseMove(e)
    if (newOffset) {
      updateOffset(newOffset.x, newOffset.y)
    }
  }, [handleMouseMove, updateOffset])

  // 处理触摸开始
  const handleTouchStartCallback = useCallback((e: React.TouchEvent): void => {
    e.preventDefault()
    handleTouchStart(e)
    
    if (e.touches.length === 2) {
      setTouchMoving(true)
    }
  }, [handleTouchStart, setTouchMoving])

  // 处理触摸移动
  const handleTouchMoveCallback = useCallback((e: React.TouchEvent): void => {
    e.preventDefault()
    
    if (e.touches.length === 2) {
      // 双指缩放
      const currentDistance = getTouchDistance(e.touches)
      handlePinchZoom(touchState.startDistance, currentDistance, touchState.startZoom)
      setTouchMoving(true)
    } else if (e.touches.length === 1 && zoom.level > 1) {
      // 单指拖动
      const touch = e.touches[0]
      if (touchState.start) {
        const newOffset = handleTouchDrag(touch, touchState.start)
        if (newOffset) {
          updateOffset(newOffset.x, newOffset.y)
          setTouchMoving(true)
        }
      }
    }
  }, [getTouchDistance, handlePinchZoom, touchState, zoom.level, handleTouchDrag, updateOffset, setTouchMoving])

  // 处理触摸结束
  const handleTouchEndCallback = useCallback((e: React.TouchEvent): void => {
    const result = handleTouchEnd(e)
    
    if (result?.swipe && result.direction) {
      if (result.direction === 'prev') {
        handlePrevImage()
      } else if (result.direction === 'next') {
        handleNextImage()
      }
    }
  }, [handleTouchEnd, handlePrevImage, handleNextImage])

  // 处理缩略图点击
  const handleThumbnailClick = useCallback((image: any): void => {
    setSelectedImage(image)
    resetZoom()
  }, [setSelectedImage, resetZoom])

  // 处理滚动到底部加载更多
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const target = e.currentTarget
    const scrollPosition = target.scrollTop + target.clientHeight
    const threshold = target.scrollHeight - 100 // 距离底部100px时加载
    
    if (scrollPosition >= threshold && hasMore && !loading) {
      loadMore()
    }
  }, [hasMore, loading, loadMore])

  if (loading && images.length === 0) {
    return (
      <div className="py-8 px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-center py-16">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-slate-600"></div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="py-8 px-4 sm:px-6 lg:px-8">
        <div className="text-center py-16">
          <p className="text-lg text-red-600 dark:text-red-400 mb-4">加载失败: {error}</p>
          <button
            onClick={() => navigate('/')}
            className="btn btn-primary px-6 py-2"
          >
            返回主页
          </button>
        </div>
      </div>
    )
  }

  if (!album) {
    return (
      <div className="py-8 px-4 sm:px-6 lg:px-8">
        <div className="text-center py-16">
          <p className="text-lg text-slate-600 dark:text-slate-400 mb-4">图集不存在</p>
          <button
            onClick={() => navigate('/')}
            className="btn btn-primary px-6 py-2"
          >
            返回主页
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8" onScroll={handleScroll} style={{ overflowY: 'auto', maxHeight: 'calc(100vh - 80px)' }}>
      <AlbumHeader album={album} onBack={() => navigate(-1)} />
      
      {/* 显示加载进度 */}
      {total > 0 && (
        <div className="mb-4 text-sm text-slate-600 dark:text-slate-400">
          已加载 {loadedCount} / {total} 张图片
          {loading && <span className="ml-2">加载中...</span>}
        </div>
      )}

      <ImageGrid 
        images={images} 
        onImageClick={handleImageClick}
        hasMore={hasMore}
        onLoadMore={loadMore}
        loading={loading}
      />

      {/* 无更多数据提示 */}
      {!hasMore && images.length > 0 && (
        <div className="text-center py-4 text-sm text-slate-400">
          已加载全部 {total} 张图片
        </div>
      )}

      <Lightbox
        isOpen={isOpen}
        selectedImage={selectedImage}
        images={images}
        zoom={zoom}
        isDragging={drag.isDragging}
        onClose={handleCloseModal}
        onPrev={handlePrevImage}
        onNext={handleNextImage}
        onThumbnailClick={handleThumbnailClick}
        onWheel={handleWheelCallback}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMoveCallback}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onTouchStart={handleTouchStartCallback}
        onTouchMove={handleTouchMoveCallback}
        onTouchEnd={handleTouchEndCallback}
      />
    </div>
  )
}

export default AlbumDetail