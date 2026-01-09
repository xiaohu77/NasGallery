import { useState, useCallback, useEffect } from 'react'
import { ImageItem } from '../types/album'

export const useImageNavigation = (images: ImageItem[], initialImage: ImageItem | null) => {
  const [selectedImage, setSelectedImage] = useState<ImageItem | null>(initialImage)

  // 切换到上一张
  const handlePrevImage = useCallback((): void => {
    if (selectedImage && images.length > 0) {
      const currentIndex = images.findIndex(img => img.id === selectedImage.id)
      const prevIndex = currentIndex > 0 ? currentIndex - 1 : images.length - 1
      setSelectedImage(images[prevIndex])
    }
  }, [selectedImage, images])

  // 切换到下一张
  const handleNextImage = useCallback((): void => {
    if (selectedImage && images.length > 0) {
      const currentIndex = images.findIndex(img => img.id === selectedImage.id)
      const nextIndex = currentIndex < images.length - 1 ? currentIndex + 1 : 0
      setSelectedImage(images[nextIndex])
    }
  }, [selectedImage, images])

  // 键盘导航
  const handleKeyDown = useCallback((e: KeyboardEvent): void => {
    if (!selectedImage) return
    
    switch(e.key) {
      case 'ArrowLeft':
        e.preventDefault()
        handlePrevImage()
        break
      case 'ArrowRight':
        e.preventDefault()
        handleNextImage()
        break
      case 'Escape':
        e.preventDefault()
        setSelectedImage(null)
        break
    }
  }, [selectedImage, handlePrevImage, handleNextImage])

  // 滑动切换（移动端）
  const handleSwipe = useCallback((deltaX: number, deltaY: number, deltaTime: number): boolean => {
    // 判断是否为滑动切换（水平移动大，垂直移动小，时间短）
    if (Math.abs(deltaX) > 50 && Math.abs(deltaY) < 30 && deltaTime < 500) {
      if (deltaX > 0) {
        handlePrevImage() // 向右滑动，上一张
      } else {
        handleNextImage() // 向左滑动，下一张
      }
      return true
    }
    return false
  }, [handlePrevImage, handleNextImage])

  // 监听键盘事件
  useEffect(() => {
    if (selectedImage) {
      document.addEventListener('keydown', handleKeyDown)
      return () => document.removeEventListener('keydown', handleKeyDown)
    }
  }, [selectedImage, handleKeyDown])

  return {
    selectedImage,
    setSelectedImage,
    handlePrevImage,
    handleNextImage,
    handleSwipe
  }
}