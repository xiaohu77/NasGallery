import { useState, useCallback } from 'react'
import { DragState, ZoomState } from '../types/album'

export const useImageDrag = (zoom: ZoomState) => {
  const [drag, setDrag] = useState<DragState>({
    isDragging: false,
    start: { x: 0, y: 0 }
  })

  // 计算最大偏移量
  const getMaxOffset = useCallback((): number => {
    return (zoom.level - 1) * 200
  }, [zoom.level])

  // 鼠标拖动开始
  const handleMouseDown = useCallback((e: React.MouseEvent): void => {
    if (zoom.level > 1) {
      setDrag({
        isDragging: true,
        start: { x: e.clientX - zoom.offset.x, y: e.clientY - zoom.offset.y }
      })
    }
  }, [zoom.level, zoom.offset])

  // 鼠标拖动中
  const handleMouseMove = useCallback((e: React.MouseEvent): { x: number; y: number } | null => {
    if (drag.isDragging && zoom.level > 1) {
      const newX = e.clientX - drag.start.x
      const newY = e.clientY - drag.start.y
      
      const maxOffset = getMaxOffset()
      const boundedX = Math.max(-maxOffset, Math.min(maxOffset, newX))
      const boundedY = Math.max(-maxOffset, Math.min(maxOffset, newY))
      
      return { x: boundedX, y: boundedY }
    }
    return null
  }, [drag.isDragging, drag.start, zoom.level, getMaxOffset])

  // 鼠标拖动结束
  const handleMouseUp = useCallback((): void => {
    setDrag(prev => ({ ...prev, isDragging: false }))
  }, [])

  // 单指拖动（移动端）
  const handleTouchDrag = useCallback((touch: React.Touch, startTouch: { x: number; y: number }): { x: number; y: number } | null => {
    if (zoom.level > 1) {
      const deltaX = touch.clientX - startTouch.x
      const deltaY = touch.clientY - startTouch.y
      
      const newX = zoom.offset.x + deltaX
      const newY = zoom.offset.y + deltaY
      
      const maxOffset = getMaxOffset()
      const boundedX = Math.max(-maxOffset, Math.min(maxOffset, newX))
      const boundedY = Math.max(-maxOffset, Math.min(maxOffset, newY))
      
      return { x: boundedX, y: boundedY }
    }
    return null
  }, [zoom.level, zoom.offset, getMaxOffset])

  return {
    drag,
    handleMouseDown,
    handleMouseMove,
    handleMouseUp,
    handleTouchDrag
  }
}