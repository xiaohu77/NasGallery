import { Album } from '../../types/album'
import { useNavigate } from 'react-router-dom'

interface AlbumHeaderProps {
  album: Album
  onBack: () => void
}

const AlbumHeader = ({ album, onBack }: AlbumHeaderProps) => {
  const navigate = useNavigate()

  const handleTagClick = (tagId: number) => {
    navigate(`/tag/${tagId}`)
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
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white">{album.title}</h1>
            <p className="text-slate-600 dark:text-slate-400 mt-1">{album.description}</p>
          </div>
        </div>
        <span className="text-sm text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 px-3 py-1 rounded-full">
          {album.imageCount} 张
        </span>
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