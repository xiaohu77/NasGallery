import { useState, useEffect } from 'react'
import { useOffline } from '../contexts/OfflineContext'
import { useTheme } from '../contexts/ThemeContext'

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<{ outcome: 'accepted' | 'dismissed' }>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

const PWAInstallPrompt = () => {
  const { isPWA } = useOffline()
  const { theme } = useTheme()
  const [showPrompt, setShowPrompt] = useState(false)
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null)

  useEffect(() => {
    // 检查是否已经安装过
    const hasInstalled = localStorage.getItem('pwa-installed')
    if (hasInstalled) return

    // 监听beforeinstallprompt事件
    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault()
      setDeferredPrompt(e as BeforeInstallPromptEvent)
      setShowPrompt(true)
    }

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt)

    // 检查是否已经在PWA模式下
    if (isPWA) {
      localStorage.setItem('pwa-installed', 'true')
      setShowPrompt(false)
    }

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
    }
  }, [isPWA])

  const handleInstall = async () => {
    if (!deferredPrompt) return

    try {
      const result = await deferredPrompt.prompt()
      if (result.outcome === 'accepted') {
        localStorage.setItem('pwa-installed', 'true')
        setShowPrompt(false)
      }
      setDeferredPrompt(null)
    } catch (error) {
      console.log('安装失败:', error)
      setShowPrompt(false)
    }
  }

  const handleDismiss = () => {
    // 记录用户选择，稍后不再提示
    localStorage.setItem('pwa-dismissed', 'true')
    setShowPrompt(false)
  }

  if (!showPrompt || isPWA) return null

  return (
    <div className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} border fixed bottom-4 left-1/2 transform -translate-x-1/2 rounded-xl shadow-lg p-4 max-w-[90%] w-[400px] flex flex-col gap-3 animate-slideUp z-50`}>
      <div className="flex items-center gap-2">
        <span className="text-xl">📱</span>
        <div className="flex-1">
          <div className={`${theme === 'dark' ? 'text-white' : 'text-gray-900'} font-bold text-base mb-0.5`}>
            安装 GirlAtlas
          </div>
          <div className={`${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'} text-sm`}>
            离线浏览图集，更快的访问速度
          </div>
        </div>
      </div>

      <div className="flex gap-2">
        <button
          onClick={handleInstall}
          className={`${theme === 'dark' ? 'bg-blue-600 hover:bg-blue-700 text-white' : 'bg-blue-500 hover:bg-blue-600 text-white'} flex-1 px-4 py-2 rounded-lg font-semibold cursor-pointer text-sm transition-colors`}
        >
          立即安装
        </button>
        <button
          onClick={handleDismiss}
          className={`${theme === 'dark' ? 'bg-gray-700 hover:bg-gray-600 text-gray-300 border-gray-600' : 'bg-gray-100 hover:bg-gray-200 text-gray-700 border-gray-300'} flex-1 px-4 py-2 rounded-lg cursor-pointer text-sm transition-colors border`}
        >
          稍后
        </button>
      </div>
    </div>
  )
}

export default PWAInstallPrompt