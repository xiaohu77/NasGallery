import { useParams, useNavigate } from 'react-router-dom'
import { useCallback, useState, useEffect } from 'react'

// Hook 导入
import { useAlbumData } from '../hooks/useAlbumData'
import { useLazyImages } from '../hooks/useLazyImages'
import { useUserData } from '../hooks/useUserData'

// 组件导入
import AlbumHeader from '../components/Album/AlbumHeader'
import ImageGrid from '../components/Album/ImageGrid'
import Lightbox from '../components/Lightbox/Lightbox'

// 服务导入
import { PWAService } from '../services/pwaService'
import { useUser } from '../contexts/UserContext'

const AlbumDetail = (): JSX.Element => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [pwaService] = useState(() => new PWAService())
  const { isAuthenticated } = useUser()
  const { recordView } = useUserData()
  
  // 数据管理
  const { album, loading: albumLoading, error: albumError } = useAlbumData(id, pwaService)
  const { images, loading: imagesLoading, error: imagesError, hasMore, loadMore, total, loadedCount } = useLazyImages(id, pwaService)
  
  const loading = albumLoading || imagesLoading
  const error = albumError || imagesError

  // 记录浏览历史
  useEffect(() => {
    if (id && isAuthenticated) {
      recordView(id)
    }
  }, [id, isAuthenticated, recordView])

  // 灯箱状态
  const [lightboxOpen, setLightboxOpen] = useState(false)
  const [lightboxIndex, setLightboxIndex] = useState(0)

  // 处理图片点击
  const handleImageClick = useCallback((image: any): void => {
    const index = images.findIndex(img => img.id === image.id)
    setLightboxIndex(index >= 0 ? index : 0)
    setLightboxOpen(true)
  }, [images])

  // 处理关闭灯箱
  const handleCloseLightbox = useCallback((): void => {
    setLightboxOpen(false)
  }, [])

  // 处理滚动
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const target = e.currentTarget
    if (target.scrollTop + target.clientHeight >= target.scrollHeight - 100 && hasMore && !loading) {
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
          <button onClick={() => navigate('/')} className="btn btn-primary px-6 py-2">返回主页</button>
        </div>
      </div>
    )
  }

  if (!album) {
    return (
      <div className="py-8 px-4 sm:px-6 lg:px-8">
        <div className="text-center py-16">
          <p className="text-lg text-slate-600 dark:text-slate-400 mb-4">图集不存在</p>
          <button onClick={() => navigate('/')} className="btn btn-primary px-6 py-2">返回主页</button>
        </div>
      </div>
    )
  }

  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8 hide-scrollbar" onScroll={handleScroll} style={{ overflowY: 'auto', maxHeight: 'calc(100vh - 80px)' }}>
      <AlbumHeader album={album} onBack={() => navigate(-1)} />
      
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

      {!hasMore && images.length > 0 && (
        <div className="text-center py-4 text-sm text-slate-400">
          已加载全部 {total} 张图片
        </div>
      )}

      <Lightbox
        isOpen={lightboxOpen}
        images={images}
        initialIndex={lightboxIndex}
        onClose={handleCloseLightbox}
      />
    </div>
  )
}

export default AlbumDetail
