import { useState, useEffect } from 'react'
import { useTheme } from '../contexts/ThemeContext'
import { useNavigate, useLocation } from 'react-router-dom'
import { PWAService } from '../services/pwaService'
import { CategoryTree } from '../types/album'

interface MenuItem {
  id: string
  name: string
  children?: MenuItem[]
  count?: number
}

const Sidebar = () => {
  const { theme } = useTheme()
  const [categories, setCategories] = useState<CategoryTree | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedMenus, setExpandedMenus] = useState<Set<string>>(new Set())
  const [isMobile, setIsMobile] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const [pwaService] = useState(() => new PWAService())

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 1024)
    }
    
    checkMobile()
    window.addEventListener('resize', checkMobile)
    
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  // 监听移动端状态变化，同步到全局
  useEffect(() => {
    const sidebar = document.querySelector<HTMLElement>('aside')
    if (sidebar) {
      if (isMobile) {
        sidebar.style.transform = mobileOpen ? 'translateX(0)' : 'translateX(-100%)'
      } else {
        // 桌面端：始终显示，重置transform
        sidebar.style.transform = 'translateX(0)'
      }
    }
  }, [mobileOpen, isMobile])

  // 加载分类数据
  useEffect(() => {
    const loadCategories = async () => {
      setLoading(true)
      setError(null)
      
      try {
        const data = await pwaService.getCategoryTree()
        setCategories(data)
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : '加载分类数据失败'
        setError(errorMessage)
        console.error('加载分类树失败:', err)
      } finally {
        setLoading(false)
      }
    }

    loadCategories()
  }, [pwaService])

  // 转换后端数据为前端需要的格式
  const menuData: MenuItem[] = categories ? [
    {
      id: 'org',
      name: '套图',
      children: categories.org.map(org => ({
        id: `org-${org.id}`,
        name: org.name,
        count: org.album_count
      }))
    },
    {
      id: 'model',
      name: '模特',
      children: categories.model.map(model => ({
        id: `model-${model.id}`,
        name: model.name,
        count: model.album_count
      }))
    },
    {
      id: 'tag',
      name: '标签',
      children: categories.tag.map(tag => ({
        id: `tag-${tag.id}`,
        name: tag.name,
        count: tag.album_count
      }))
    }
  ] : []

  const toggleMenu = (id: string) => {
    const newExpanded = new Set(expandedMenus)
    if (newExpanded.has(id)) {
      newExpanded.delete(id)
    } else {
      newExpanded.add(id)
    }
    setExpandedMenus(newExpanded)
  }

  const toggleMobileSidebar = () => {
    setMobileOpen(!mobileOpen)
  }

  // 处理分类点击
  const handleCategoryClick = (categoryType: string, categoryId: number, categoryName: string) => {
    // 提取类型（org, model, tag）
    const type = categoryType.split('-')[0] as 'org' | 'model' | 'tag'
    
    // 构建不同路由路径
    let routePath = '/'
    if (type === 'org') {
      routePath = `/org/${categoryId}`
    } else if (type === 'model') {
      routePath = `/model/${categoryId}`
    } else if (type === 'tag') {
      routePath = `/tag/${categoryId}`
    }
    
    // 添加分类名称到查询参数
    const params = new URLSearchParams({ name: categoryName })
    routePath += `?${params.toString()}`
    
    // 导航到对应路由
    navigate(routePath)
    
    // 移动端自动关闭侧边栏
    if (isMobile) {
      setMobileOpen(false)
    }
  }

  // 暴露方法给Header调用
  useEffect(() => {
    window.toggleSidebar = toggleMobileSidebar
    return () => {
      delete window.toggleSidebar
    }
  }, [mobileOpen, isMobile])

  // 重新加载分类数据
  const reloadCategories = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await pwaService.refreshCategoryTree()
      setCategories(data)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '加载分类数据失败'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  // 加载状态 - 优化：只在初始加载时显示
  if (loading && !categories) {
    return (
      <aside className="fixed top-12 left-0 h-[calc(100vh-3rem)] w-64 bg-white/80 dark:bg-black/80 backdrop-blur-md z-40 overflow-y-auto hide-scrollbar">
        <div className="p-4 text-center text-sm text-gray-500">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-slate-600 mx-auto mb-2"></div>
          加载中...
        </div>
      </aside>
    )
  }

  // 错误状态
  if (error) {
    return (
      <aside className="fixed top-12 left-0 h-[calc(100vh-3rem)] w-64 bg-white/80 dark:bg-black/80 backdrop-blur-md z-40 overflow-y-auto hide-scrollbar">
        <div className="p-4 text-center text-sm text-red-500">
          <p className="mb-2">{error}</p>
          <button
            onClick={reloadCategories}
            className="text-xs underline hover:text-red-600 dark:hover:text-red-400"
          >
            点击重试
          </button>
        </div>
      </aside>
    )
  }

  // 空数据状态
  if (!categories || menuData.every(menu => !menu.children || menu.children.length === 0)) {
    return (
      <aside className="fixed top-12 left-0 h-[calc(100vh-3rem)] w-64 bg-white/80 dark:bg-black/80 backdrop-blur-md z-40 overflow-y-auto hide-scrollbar">
        <div className="p-4 text-center text-sm text-gray-500">
          暂无分类数据
        </div>
      </aside>
    )
  }

  return (
    <>
      {/* 侧边栏 */}
      <aside
        className={`fixed top-12 left-0 h-[calc(100vh-3rem)] w-64 bg-white/80 dark:bg-black/80 backdrop-blur-md transition-transform duration-300 z-40 overflow-y-auto hide-scrollbar ${
          isMobile ? (mobileOpen ? 'translate-x-0' : '-translate-x-full') : 'translate-x-0'
        } ${isMobile ? 'shadow-2xl' : ''}`}
      >
        <div className="p-3 sm:p-4">
          <nav className={isMobile ? '' : 'pt-2'}>
            {menuData.map((menu) => (
              <div key={menu.id} className="mb-2">
                <button
                  onClick={() => toggleMenu(menu.id)}
                  className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-slate-700 dark:text-slate-300 hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors text-sm"
                >
                  <span className="font-medium">{menu.name}</span>
                  <svg
                    className={`w-3 h-3 transition-transform duration-200 ${
                      expandedMenus.has(menu.id) ? 'rotate-180' : ''
                    }`}
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    viewBox="0 0 24 24"
                  >
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                </button>

                {menu.children && expandedMenus.has(menu.id) && (
                  <div className="ml-4 mt-1 space-y-1 border-l-2 border-gray-200 dark:border-gray-700 pl-3">
                    {menu.children.map((child) => (
                      <button
                        key={child.id}
                        onClick={() => handleCategoryClick(menu.id, parseInt(child.id.split('-')[1]), child.name)}
                        className="w-full text-left px-3 py-1.5 rounded text-sm text-slate-600 dark:text-slate-400 hover:bg-gray-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white transition-colors flex justify-between items-center"
                      >
                        <span>{child.name}</span>
                        {child.count !== undefined && (
                          <span className="text-xs text-gray-400 bg-gray-100 dark:bg-slate-800 px-1.5 py-0.5 rounded">
                            {child.count}
                          </span>
                        )}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </nav>
        </div>
      </aside>

      {/* 移动端遮罩 */}
      {isMobile && mobileOpen && (
        <div
          onClick={() => setMobileOpen(false)}
          className="fixed inset-0 bg-black/50 z-30"
        />
      )}
    </>
  )
}

export default Sidebar