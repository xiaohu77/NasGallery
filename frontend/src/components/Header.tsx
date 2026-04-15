import { useNavigate, useLocation } from 'react-router-dom'
import { useTheme } from '../contexts/ThemeContext'
import { useUser } from '../contexts/UserContext'
import { SunIcon, MoonIcon, UserIcon, SettingsIcon, LogoutIcon } from './icons'
import { useState, useEffect, useCallback } from 'react'
import SearchBox from './SearchBox'
import { aiService } from '../services/aiService'
import { PWAService } from '../services/pwaService'

interface SubCategory {
  id: number
  name: string
  count: number
}

const mainTabs = [
  { id: 'all', label: '所有图集', path: '/' },
  { id: 'org', label: '刊物', path: '/org' },
  { id: 'model', label: '人物', path: '/model' },
  { id: 'cosplayer', label: 'Cosplayer', path: '/cosplayer' },
  { id: 'character', label: '角色', path: '/character' },
]

const allSubTabs = [
  { id: 'recent', label: '近期新增', sort: 'recent' },
  { id: 'popular', label: '浏览最多', sort: 'popular' },
  { id: 'favorites', label: '我的收藏', sort: 'favorites', requiresAuth: true },
  { id: 'history', label: '历史浏览', sort: 'history', requiresAuth: true },
]

const Header = () => {
  const { theme, toggleTheme } = useTheme()
  const { user, isAuthenticated, logout } = useUser()
  const navigate = useNavigate()
  const location = useLocation()
  const [showUserMenu, setShowUserMenu] = useState(false)
  const [aiEnabled, setAiEnabled] = useState(false)
  const [activeMainTab, setActiveMainTab] = useState('all')
  const [activeSubTab, setActiveSubTab] = useState<string | null>(null)
  const [subCategories, setSubCategories] = useState<SubCategory[]>([])
  const [pwaService] = useState(() => new PWAService())

  useEffect(() => {
    const checkAiStatus = async () => {
      try {
        const status = await aiService.getStatus()
        setAiEnabled(status.has_model_files || status.stats.embedded_albums > 0)
      } catch (e) {
        setAiEnabled(false)
      }
    }
    checkAiStatus()
  }, [])

  // 是否显示 Tab 栏
  const showTabs = !location.pathname.startsWith('/album/') && 
                   !location.pathname.startsWith('/login') && 
                   !location.pathname.startsWith('/settings') &&
                   !location.pathname.startsWith('/about')

  // 根据当前路径设置活跃 tab
  useEffect(() => {
    if (!showTabs) return

    const path = location.pathname
    const params = new URLSearchParams(location.search)
    
    if (path.startsWith('/org')) {
      setActiveMainTab('org')
      const orgId = path.split('/')[2]
      setActiveSubTab(orgId || null)
    } else if (path.startsWith('/model')) {
      setActiveMainTab('model')
      const modelId = path.split('/')[2]
      setActiveSubTab(modelId || null)
    } else if (path.startsWith('/cosplayer')) {
      setActiveMainTab('cosplayer')
      const cosplayerId = path.split('/')[2]
      setActiveSubTab(cosplayerId || null)
    } else if (path.startsWith('/character')) {
      setActiveMainTab('character')
      const characterId = path.split('/')[2]
      setActiveSubTab(characterId || null)
    } else {
      setActiveMainTab('all')
      const sort = params.get('sort')
      setActiveSubTab(sort || null)
    }
  }, [location.pathname, location.search, showTabs])

  // 获取子分类数据
  useEffect(() => {
    const fetchSubCategories = async () => {
      if (activeMainTab === 'all') {
        setSubCategories([])
        return
      }

      try {
        const categories = await pwaService.getCategoryTree()
        if (activeMainTab === 'org') {
          setSubCategories(categories.org.map((o: any) => ({
            id: o.id,
            name: o.name,
            count: o.album_count
          })))
        } else if (activeMainTab === 'model') {
          setSubCategories(categories.model.map((m: any) => ({
            id: m.id,
            name: m.name,
            count: m.album_count
          })))
        } else if (activeMainTab === 'cosplayer') {
          setSubCategories(categories.cosplayer.map((c: any) => ({
            id: c.id,
            name: c.name,
            count: c.album_count
          })))
        } else if (activeMainTab === 'character') {
          setSubCategories(categories.character.map((c: any) => ({
            id: c.id,
            name: c.name,
            count: c.album_count
          })))
        }
      } catch (e) {
        console.error('获取子分类失败:', e)
        setSubCategories([])
      }
    }
    fetchSubCategories()
  }, [activeMainTab, pwaService])

  const handleLogoClick = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    navigate('/', { replace: true })
  }, [navigate])

  const handleMainTabClick = (tabId: string, path: string) => {
    if (tabId !== 'all' && subCategories.length > 0) {
      const firstSubCategory = subCategories[0]
      if (tabId === 'org') {
        navigate(`/org/${firstSubCategory.id}`)
      } else if (tabId === 'model') {
        navigate(`/model/${firstSubCategory.id}`)
      } else if (tabId === 'cosplayer') {
        navigate(`/cosplayer/${firstSubCategory.id}`)
      } else if (tabId === 'character') {
        navigate(`/character/${firstSubCategory.id}`)
      }
      return
    }
    setActiveSubTab(null)
    navigate(path)
  }

  const handleSubTabClick = (subId: string, subName?: string) => {
    // 收藏和历史浏览使用查询参数
    if (subId === 'favorites' || subId === 'history') {
      if (!isAuthenticated) {
        navigate('/login')
        return
      }
      navigate(`/?sort=${subId}`)
      return
    }
    
    if (activeMainTab === 'all') {
      navigate(`/?sort=${subId}`)
    } else if (activeMainTab === 'org') {
      navigate(`/org/${subId}`)
    } else if (activeMainTab === 'model') {
      navigate(`/model/${subId}`)
    } else if (activeMainTab === 'cosplayer') {
      navigate(`/cosplayer/${subId}`)
    } else if (activeMainTab === 'character') {
      navigate(`/character/${subId}`)
    }
  }

  const handleSearch = useCallback((query: string, mode: 'normal' | 'ai' = 'normal') => {
    if (query) {
      navigate(`/?search=${encodeURIComponent(query)}&mode=${mode}`)
    } else {
      navigate('/')
    }
  }, [navigate])

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

  const handleSettings = () => {
    navigate('/settings')
    setShowUserMenu(false)
  }

  const handleAbout = () => {
    navigate('/about')
    setShowUserMenu(false)
  }

  return (
    <header className="fixed top-0 left-0 right-0 z-50 glass">
      {/* 主导航栏 */}
      <div className="flex items-center h-12 px-4 sm:px-6">
        <button
          onClick={handleLogoClick}
          className="text-sm font-semibold text-gray-900 dark:text-white hover:opacity-80 transition-opacity"
        >
          NasGallery
        </button>

        <div className="flex-1 flex justify-center mx-4">
          <div className="w-full max-w-xs sm:max-w-sm">
            <SearchBox onSearch={handleSearch} placeholder="搜索..." aiEnabled={aiEnabled} />
          </div>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={toggleTheme}
            className="p-2 rounded-full hover:bg-gray-500/10 transition-colors active:scale-90"
            aria-label="切换主题"
          >
            {theme === 'light' ? (
              <MoonIcon className="w-4 h-4 text-gray-700 dark:text-gray-300" />
            ) : (
              <SunIcon className="w-4 h-4 text-gray-700 dark:text-gray-300" />
            )}
          </button>

          <div className="relative">
            <button
              onClick={handleUserClick}
              className="p-2 rounded-full hover:bg-gray-500/10 transition-colors active:scale-90"
              aria-label={isAuthenticated ? '用户菜单' : '登录'}
            >
              <UserIcon className="w-4 h-4 text-gray-700 dark:text-gray-300" />
            </button>

            {showUserMenu && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setShowUserMenu(false)} />
                <div className="absolute right-0 top-full mt-2 w-56 glass-card rounded-2xl shadow-xl py-2 z-50 animate-bounce-in">
                  <div className="px-4 py-3 border-b border-gray-200/30 dark:border-gray-700/30">
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {user?.username}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                      {user?.email}
                    </p>
                  </div>
                  <button
                    onClick={handleSettings}
                    className="w-full px-4 py-2.5 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-500/10 flex items-center gap-3 transition-colors"
                  >
                    <SettingsIcon className="w-4 h-4" />
                    设置
                  </button>
                  <button
                    onClick={handleAbout}
                    className="w-full px-4 py-2.5 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-500/10 flex items-center gap-3 transition-colors"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    关于
                  </button>
                  <button
                    onClick={handleLogout}
                    className="w-full px-4 py-2.5 text-left text-sm text-red-500 hover:bg-red-500/10 flex items-center gap-3 transition-colors"
                  >
                    <LogoutIcon className="w-4 h-4" />
                    退出登录
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* 一级 Tab 栏 */}
      {showTabs && (
        <div className="flex items-center gap-6 px-4 sm:px-6 pb-1 overflow-x-auto hide-scrollbar">
          {mainTabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => handleMainTabClick(tab.id, tab.path)}
              className={`
                py-1.5 text-xs font-medium whitespace-nowrap transition-all
                ${activeMainTab === tab.id
                  ? 'text-gray-900 dark:text-white border-b-2 border-gray-900 dark:border-white'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                }
              `}
            >
              {tab.label}
            </button>
          ))}
        </div>
      )}

      {/* 二级 Tab 栏 */}
      {showTabs && (
        <div className="flex items-center gap-4 px-4 sm:px-6 pb-1 overflow-x-auto hide-scrollbar border-b border-gray-200/30 dark:border-gray-700/30">
          {/* 所有图集的排序选项 */}
          {activeMainTab === 'all' && allSubTabs.map((sub) => {
            // 未登录时隐藏需要认证的Tab
            if (sub.requiresAuth && !isAuthenticated) return null
            return (
              <button
                key={sub.id}
                onClick={() => handleSubTabClick(sub.sort)}
                className={`
                  py-1 text-xs whitespace-nowrap transition-all
                  ${activeSubTab === sub.sort
                    ? 'text-gray-900 dark:text-white'
                    : 'text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-400'
                  }
                `}
              >
                {sub.label}
              </button>
            )
          })}
          
          {/* 刊物/人物/Cosplayer/角色的子分类 */}
          {(activeMainTab === 'org' || activeMainTab === 'model' || activeMainTab === 'cosplayer' || activeMainTab === 'character') && subCategories.map((sub) => (
            <button
              key={sub.id}
              onClick={() => handleSubTabClick(sub.id.toString())}
              className={`
                py-1 text-xs whitespace-nowrap transition-all
                ${activeSubTab === sub.id.toString()
                  ? 'text-gray-900 dark:text-white'
                  : 'text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-400'
                }
              `}
            >
              {sub.name} <span className="opacity-60">{sub.count}</span>
            </button>
          ))}
        </div>
      )}
    </header>
  )
}

export default Header
