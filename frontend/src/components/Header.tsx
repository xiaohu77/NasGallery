import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useTheme } from '../contexts/ThemeContext'
import { useUser } from '../contexts/UserContext'
import { SunIcon, MoonIcon, UserIcon } from './icons'
import { useState, useEffect, useCallback } from 'react'
import SearchBox from './SearchBox'

declare global {
  interface Window {
    toggleSidebar?: () => void
  }
}

const Header = () => {
  const { theme, toggleTheme } = useTheme()
  const { user, isAuthenticated, logout } = useUser()
  const navigate = useNavigate()
  const location = useLocation()
  const [isMobile, setIsMobile] = useState(false)
  const [showUserMenu, setShowUserMenu] = useState(false)

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 1024)
    }
    
    checkMobile()
    window.addEventListener('resize', checkMobile)
    
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  const toggleSidebar = () => {
    if (window.toggleSidebar) {
      window.toggleSidebar()
    }
  }

  const handleSearch = useCallback((query: string) => {
    const params = new URLSearchParams(location.search)
    if (query) {
      params.set('search', query)
    } else {
      params.delete('search')
    }
    navigate(`${location.pathname}?${params.toString()}`, { replace: true })
  }, [navigate, location])

  const handleUserClick = () => {
    if (isAuthenticated) {
      setShowUserMenu(!showUserMenu)
    } else {
      navigate('/login')
    }
  }

  const handleLogout = () => {
    logout()
    setShowUserMenu(false)
    navigate('/')
  }

  const handleUserPage = () => {
    navigate('/user')
    setShowUserMenu(false)
  }

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-white/80 dark:bg-black/80 backdrop-blur-md border-b border-gray-200 dark:border-gray-800">
      <div className="flex items-center justify-between h-12 px-3 sm:px-4 lg:px-6">
        <div className="flex items-center gap-2">
          {isMobile && (
            <button
              onClick={toggleSidebar}
              className="btn btn-ghost p-1.5 rounded-lg"
              aria-label="打开侧边栏"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="3" y1="6" x2="21" y2="6" />
                <line x1="3" y1="18" x2="21" y2="18" />
              </svg>
            </button>
          )}
          <Link to="/" className="text-sm font-bold text-slate-900 dark:text-white hover:opacity-80 transition-opacity">
            GirlAtlas
          </Link>
        </div>
        
        {/* 搜索框 - 收窄宽度 */}
        <div className="flex-1 max-w-[12rem] mx-3">
          <SearchBox onSearch={handleSearch} placeholder="搜索..." />
        </div>
        
        <div className="flex items-center gap-1">
          <button
            onClick={toggleTheme}
            className="btn btn-ghost p-1.5 rounded-lg"
            aria-label="切换主题"
          >
            {theme === 'light' ? (
              <MoonIcon className="w-4 h-4" />
            ) : (
              <SunIcon className="w-4 h-4" />
            )}
          </button>
          
          {/* 用户图标 */}
          <div className="relative">
            <button
              onClick={handleUserClick}
              className="btn btn-ghost p-1.5 rounded-lg"
              aria-label={isAuthenticated ? '用户菜单' : '登录'}
            >
              <UserIcon className="w-4 h-4" />
            </button>
            
            {/* 用户下拉菜单 */}
            {showUserMenu && (
              <div className="absolute right-0 top-full mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-2 z-50">
                <div className="px-4 py-2 border-b border-gray-200 dark:border-gray-700">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    {user?.username}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {user?.email}
                  </p>
                </div>
                <button
                  onClick={handleUserPage}
                  className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  个人中心
                </button>
                <button
                  onClick={handleLogout}
                  className="w-full px-4 py-2 text-left text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
                >
                  退出登录
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header