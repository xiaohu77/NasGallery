import { Album } from '../../types/album'

interface AlbumHeaderProps {
  album: Album
  onBack: () => void
}

const AlbumHeader = ({ album, onBack }: AlbumHeaderProps) => {
  return (
    <div className="mb-6 flex items-center justify-between">
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
      <span className="text-sm text-slate-600 dark:text-slate-400 bg-slate-100 dark:bg-slate-900 px-3 py-1 rounded-full">
        {album.imageCount} 张
      </span>
    </div>
  )
}

export default AlbumHeader