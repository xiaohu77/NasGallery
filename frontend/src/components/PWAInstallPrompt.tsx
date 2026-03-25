import { useState, useEffect } from 'react'
import { useOffline } from '../contexts/OfflineContext'
import { useUser } from '../contexts/UserContext'

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<{ outcome: 'accepted' | 'dismissed' }>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

const PWAInstallPrompt = () => {
  const { isPWA } = useOffline()
  const { isAuthenticated } = useUser()
  const [showPrompt, setShowPrompt] = useState(false)
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null)

  useEffect(() => {
    // 已安装或已PWA模式，不显示
    if (isPWA) {
      localStorage.setItem('pwa-installed', 'true')
      return
    }

    // 已安装，不显示
    const hasInstalled = localStorage.getItem('pwa-installed')
    if (hasInstalled) return

    // 已关闭提示，不显示
    const hasDismissed = localStorage.getItem('pwa-dismissed')
    if (hasDismissed) return

    // 只有登录用户才显示提示
    if (!isAuthenticated) return

    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault()
      setDeferredPrompt(e as BeforeInstallPromptEvent)
      // 延迟显示，让用户先看到界面
      setTimeout(() => {
        setShowPrompt(true)
      }, 2000)
    }

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt)

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
    }
  }, [isPWA, isAuthenticated])

  const handleInstall = async () => {
    if (!deferredPrompt) return

    try {
      const result = await deferredPrompt.prompt()
      if (result.outcome === 'accepted') {
        localStorage.setItem('pwa-installed', 'true')
      }
      setShowPrompt(false)
      setDeferredPrompt(null)
    } catch (error) {
      console.log('安装失败:', error)
      setShowPrompt(false)
    }
  }

  const handleDismiss = () => {
    localStorage.setItem('pwa-dismissed', 'true')
    setShowPrompt(false)
  }

  if (!showPrompt || isPWA) return null

  return (
    <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 w-[90%] max-w-[360px] animate-bounce-in-up">
      <div className="glass-card rounded-3xl shadow-xl p-5">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-2xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
            <svg className="w-5 h-5 text-gray-600 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
          </div>
          <div>
            <div className="font-semibold text-gray-900 dark:text-white text-sm">
              安装 NasGallery
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              离线浏览，更快访问
            </div>
          </div>
        </div>

        <div className="flex gap-2">
          <button
            onClick={handleInstall}
            className="flex-1 btn btn-primary rounded-2xl py-2.5"
          >
            安装
          </button>
          <button
            onClick={handleDismiss}
            className="flex-1 btn btn-ghost rounded-2xl py-2.5 bg-gray-500/10"
          >
            稍后
          </button>
        </div>
      </div>
    </div>
  )
}

export default PWAInstallPrompt
