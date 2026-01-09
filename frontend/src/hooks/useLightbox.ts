import { useState, useCallback, useEffect } from 'react'
import { ImageItem, TouchState } from '../types/album'

export const useLightbox = (images: ImageItem[]) => {
  const [isOpen, setIsOpen] = useState(false)
  const [touchState, setTouchState] = useState<TouchState>({
    start: null,
    startDistance: 0,
    startZoom: 1,
    isMoving: false
  })

  // 计算两点距离
  const getTouchDistance = useCallback((touches: React.TouchList): number => {
    const touch1 = touches[0]
    const touch2 = touches[1]
    const dx = touch1.clientX - touch2.clientX
    const dy = touch1.clientY - touch2.clientY
    return Math.sqrt(dx * dx + dy * dy)
  }, [])

  // 触摸开始
  const handleTouchStart = useCallback((e: React.TouchEvent): void => {
    e.preventDefault()
    
    if (e.touches.length === 1) {
      const touch = e.touches[0]
      setTouchState({
        start: { x: touch.clientX, y: touch.clientY, time: Date.now() },
        startDistance: 0,
        startZoom: 1,
        isMoving: false
      })
    } else if (e.touches.length === 2) {
      const distance = getTouchDistance(e.touches)
      setTouchState(prev => ({
        ...prev,
        startDistance: distance,
        startZoom: 1,
        start: null
      }))
    }
  }, [getTouchDistance])

  // 触摸移动
  const handleTouchMove = useCallback((e: React.TouchEvent): { type: string; distance?: number; touch?: React.Touch; startTouch?: { x: number; y: number; time: number } } | null => {
    e.preventDefault()
    
    if (e.touches.length === 2) {
      return { type: 'pinch', distance: getTouchDistance(e.touches) }
    } else if (e.touches.length === 1 && touchState.start) {
      const touch = e.touches[0]
      return {
        type: 'drag',
        touch,
        startTouch: touchState.start
      }
    }
    return null
  }, [touchState.start, getTouchDistance])

  // 触摸结束
  const handleTouchEnd = useCallback((e: React.TouchEvent): { swipe: boolean; direction: 'prev' | 'next' | null } | null => {
    e.preventDefault()
    
    if (e.touches.length === 0 && touchState.start && !touchState.isMoving) {
      const touchEndX = e.changedTouches[0].clientX
      const touchEndY = e.changedTouches[0].clientY
      const touchEndTime = Date.now()
      
      const deltaX = touchEndX - touchState.start.x
      const deltaY = touchEndY - touchState.start.y
      const deltaTime = touchEndTime - touchState.start.time
      
      if (Math.abs(deltaX) > 50 && Math.abs(deltaY) < 30 && deltaTime < 500) {
        return {
          swipe: true,
          direction: deltaX > 0 ? 'prev' : 'next'
        }
      }
    }
    
    // 重置状态
    setTouchState({
      start: null,
      startDistance: 0,
      startZoom: 1,
      isMoving: false
    })
    
    return null
  }, [touchState])

  // 设置移动状态
  const setTouchMoving = useCallback((moving: boolean): void => {
    setTouchState(prev => ({ ...prev, isMoving: moving }))
  }, [])

  // 锁定背景滚动
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
      
      const preventScroll = (e: TouchEvent) => {
        if (e.target === document.body || e.target === document.documentElement) {
          e.preventDefault()
        }
      }
      
      document.addEventListener('touchmove', preventScroll, { passive: false })
      
      return () => {
        document.body.style.overflow = ''
        document.removeEventListener('touchmove', preventScroll)
      }
    }
  }, [isOpen])

  return {
    isOpen,
    setIsOpen,
    touchState,
    handleTouchStart,
    handleTouchMove,
    handleTouchEnd,
    setTouchMoving,
    getTouchDistance
  }
}