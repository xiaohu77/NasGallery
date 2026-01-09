import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { registerServiceWorker, checkNetworkStatus, listenToNetworkChanges } from '../utils/pwa'

interface OfflineContextType {
  isOnline: boolean
  isPWA: boolean
  isSWRegistered: boolean
  showOfflineIndicator: boolean
  toggleOfflineIndicator: (show: boolean) => void
  refreshData: () => Promise<void>
}

const OfflineContext = createContext<OfflineContextType | undefined>(undefined)

export const OfflineProvider = ({ children }: { children: ReactNode }) => {
  const [isOnline, setIsOnline] = useState<boolean>(true)
  const [isPWA, setIsPWA] = useState<boolean>(false)
  const [isSWRegistered, setIsSWRegistered] = useState<boolean>(false)
  const [showOfflineIndicator, setShowOfflineIndicator] = useState<boolean>(false)

  useEffect(() => {
    // 检查是否为PWA模式
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent)
    const isStandaloneIOS = (window.navigator as any).standalone === true
    
    setIsPWA(isStandalone || isStandaloneIOS)

    // 检查初始网络状态
    setIsOnline(checkNetworkStatus())

    // 监听网络变化
    listenToNetworkChanges((online) => {
      setIsOnline(online)
      if (!online) {
        setShowOfflineIndicator(true)
      }
    })

    // 注册Service Worker
    if ('serviceWorker' in navigator) {
      registerServiceWorker().then(() => {
        setIsSWRegistered(true)
      }).catch(() => {
        setIsSWRegistered(false)
      })
    }
  }, [])

  const toggleOfflineIndicator = (show: boolean) => {
    setShowOfflineIndicator(show)
  }

  const refreshData = async () => {
    // 仅触发页面重新加载，不再清理缓存
    window.location.reload()
  }

  return (
    <OfflineContext.Provider value={{
      isOnline,
      isPWA,
      isSWRegistered,
      showOfflineIndicator,
      toggleOfflineIndicator,
      refreshData
    }}>
      {children}
      {/* 离线指示器 */}
      {showOfflineIndicator && !isOnline && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          background: '#f59e0b',
          color: 'white',
          padding: '8px 16px',
          textAlign: 'center',
          fontSize: '14px',
          zIndex: 9999,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '8px'
        }}>
          <span>📡 离线模式 - 无法获取新数据</span>
          <button 
            onClick={() => setShowOfflineIndicator(false)}
            style={{
              background: 'rgba(255,255,255,0.2)',
              border: '1px solid white',
              color: 'white',
              padding: '2px 8px',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            关闭
          </button>
        </div>
      )}
    </OfflineContext.Provider>
  )
}

export const useOffline = () => {
  const context = useContext(OfflineContext)
  if (!context) {
    throw new Error('useOffline must be used within OfflineProvider')
  }
  return context
}