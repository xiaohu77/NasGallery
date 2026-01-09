import { useState, useEffect } from 'react'
import { useOffline } from '../contexts/OfflineContext'

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<{ outcome: 'accepted' | 'dismissed' }>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

const PWAInstallPrompt = () => {
  const { isPWA } = useOffline()
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
    <div style={{
      position: 'fixed',
      bottom: '20px',
      left: '50%',
      transform: 'translateX(-50%)',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      color: 'white',
      padding: '16px 20px',
      borderRadius: '12px',
      boxShadow: '0 8px 24px rgba(0,0,0,0.2)',
      zIndex: 10000,
      maxWidth: '90%',
      width: '400px',
      display: 'flex',
      flexDirection: 'column',
      gap: '12px',
      animation: 'slideUp 0.3s ease-out'
    }}>
      <style>{`
        @keyframes slideUp {
          from { transform: translateX(-50%) translateY(100%); opacity: 0; }
          to { transform: translateX(-50%) translateY(0); opacity: 1; }
        }
      `}</style>
      
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ fontSize: '20px' }}>📱</span>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 'bold', fontSize: '16px', marginBottom: '2px' }}>
            安装 GirlAtlas
          </div>
          <div style={{ fontSize: '13px', opacity: 0.9 }}>
            离线浏览图集，更快的访问速度
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '8px' }}>
        <button
          onClick={handleInstall}
          style={{
            flex: 1,
            background: 'white',
            color: '#667eea',
            border: 'none',
            padding: '10px 16px',
            borderRadius: '8px',
            fontWeight: 'bold',
            cursor: 'pointer',
            fontSize: '14px'
          }}
        >
          立即安装
        </button>
        <button
          onClick={handleDismiss}
          style={{
            flex: 1,
            background: 'transparent',
            color: 'white',
            border: '1px solid rgba(255,255,255,0.5)',
            padding: '10px 16px',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '14px'
          }}
        >
          稍后
        </button>
      </div>
    </div>
  )
}

export default PWAInstallPrompt