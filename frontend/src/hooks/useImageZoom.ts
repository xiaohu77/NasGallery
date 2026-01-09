import { useState, useCallback } from 'react'
import { ZoomState } from '../types/album'

export const useImageZoom = () => {
  const [zoom, setZoom] = useState<ZoomState>({
    level: 1,
    offset: { x: 0, y: 0 }
  })

  // 鼠标滚轮缩放
  const handleWheel = useCallback((e: React.WheelEvent): void => {
    e.preventDefault()
    const delta = e.deltaY > 0 ? -0.1 : 0.1
    const newLevel = Math.max(1, Math.min(3, zoom.level + delta))
    
    setZoom({
      level: newLevel,
      offset: newLevel === 1 ? { x: 0, y: 0 } : zoom.offset
    })
  }, [zoom.level, zoom.offset])

  // 双指缩放
  const handlePinchZoom = useCallback((startDistance: number, currentDistance: number, startZoom: number): void => {
    const scale = currentDistance / startDistance
    const newLevel = Math.max(1, Math.min(3, startZoom * scale))
    
    setZoom(prev => ({
      level: newLevel,
      offset: newLevel === 1 ? { x: 0, y: 0 } : prev.offset
    }))
  }, [])

  // 重置缩放
  const resetZoom = useCallback((): void => {
    setZoom({ level: 1, offset: { x: 0, y: 0 } })
  }, [])

  // 更新偏移
  const updateOffset = useCallback((x: number, y: number): void => {
    setZoom(prev => ({ ...prev, offset: { x, y } }))
  }, [])

  return {
    zoom,
    handleWheel,
    handlePinchZoom,
    resetZoom,
    updateOffset
  }
}