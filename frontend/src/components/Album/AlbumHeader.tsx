import { Album } from '../../types/album'
import { useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { useUser } from '../../contexts/UserContext'

interface AlbumHeaderProps {
  album: Album
  onBack: () => void
}

const API_BASE = import.meta.env.DEV
  ? (import.meta.env.VITE_API_BASE || 'http://localhost:8000')
  : window.location.origin

const AlbumHeader = ({ album, onBack }: AlbumHeaderProps) => {
  const navigate = useNavigate()
  const { token, isAuthenticated } = useUser()
  const [isFavorited, setIsFavorited] = useState(false)
  const [favoriting, setFavoriting] = useState(false)

  const handleTagClick = (tagId: number) => {
    navigate(`/tag/${tagId}`)
  }

  useEffect(() => {
    if (!token) return

    const checkFavorite = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/user/favorites/check/${album.id}`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        const data = await res.json()
        setIsFavorited(data.is_favorited)
      } catch (e) {
        console.error('检查收藏状态失败:', e)
      }
    }
    checkFavorite()
  }, [album.id, token])

  const handleFavorite = async () => {
    if (!token) {
      navigate('/login')
      return
    }

    setFavoriting(true)
    try {
      const method = isFavorited ? 'DELETE' : 'POST'
      await fetch(`${API_BASE}/api/user/favorites/${album.id}`, {
        method,
        headers: { Authorization: `Bearer ${token}` }
      })
      setIsFavorited(!isFavorited)
    } catch (e) {
      console.error('操作收藏失败:', e)
    } finally {
      setFavoriting(false)
    }
  }

  return (
    <div className="mb-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4">
          <button
            onClick={onBack}
            className="btn btn-ghost p-2 rounded-lg"
            aria-label="返回"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <line x1="19" y1="12" x2="5" y2="12" />
              <polyline points="12 19 5 12 12 5" />
            </svg>
          </button>
          <div className="min-w-0">
            <h1 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white break-words">{album.title}</h1>
            {album.description && (
              <p className="text-slate-600 dark:text-slate-400 mt-1 text-sm break-words">{album.description}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleFavorite}
            disabled={favoriting}
            className={`p-2 rounded-lg transition-colors ${isFavorited ? 'text-red-500' : 'text-slate-400 hover:text-red-500'}`}
            aria-label={isFavorited ? '取消收藏' : '添加收藏'}
          >
            <svg className="w-5 h-5" fill={isFavorited ? 'currentColor' : 'none'} stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
            </svg>
          </button>
          {album.viewCount !== undefined && album.viewCount > 0 && (
            <span className="text-sm text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 px-3 py-1 rounded-full">
              {album.viewCount} 浏览
            </span>
          )}
          <span className="text-sm text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 px-3 py-1 rounded-full">
            {album.imageCount} 张
          </span>
        </div>
      </div>
      
      {/* 标签展示区域 */}
      {album.tags && album.tags.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 mt-3 ml-14">
          {album.tags.map((tag) => (
            <button
              key={tag.id}
              onClick={() => handleTagClick(tag.id)}
              className="group inline-flex items-center px-3 py-1.5 text-sm font-medium text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-md transition-all duration-200 cursor-pointer"
            >
              <svg className="w-3.5 h-3.5 mr-1.5 text-slate-400 group-hover:text-slate-500 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
              </svg>
              {tag.name}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export default AlbumHeader