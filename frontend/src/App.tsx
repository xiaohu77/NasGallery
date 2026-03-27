import { Routes, Route, useLocation, Navigate } from 'react-router-dom'
import { ThemeProvider } from './contexts/ThemeContext'
import { OfflineProvider } from './contexts/OfflineContext'
import { UserProvider } from './contexts/UserContext'
import { useUser } from './contexts/UserContext'
import Layout from './components/Layout'
import PWAInstallPrompt from './components/PWAInstallPrompt'
import Home from './pages/Home'
import AlbumDetail from './pages/AlbumDetail'
import Login from './pages/Login'
import Settings from './pages/Settings'

// 创建一个包装组件来管理 Home 页面的 key
const HomeWrapper = () => {
  const location = useLocation();
  
  // 为不同路径的 Home 组件生成不同的 key
  // 这样可以确保不同分类的列表页使用不同的组件实例
  // 但同一分类下，从详情页返回时不会重新挂载
  const getKey = () => {
    const path = location.pathname;
    if (path === '/') return 'home-all';
    if (path === '/org') return 'home-org';
    if (path === '/model') return 'home-model';
    if (path === '/cosplayer') return 'home-cosplayer';
    if (path === '/character') return 'home-character';
    if (path.startsWith('/org/')) return 'home-org-detail';
    if (path.startsWith('/model/')) return 'home-model-detail';
    if (path.startsWith('/cosplayer/')) return 'home-cosplayer-detail';
    if (path.startsWith('/character/')) return 'home-character-detail';
    if (path.startsWith('/tag/')) return 'home-tag';
    return 'home';
  };

  return <Home key={getKey()} />;
};

// 包装详情页组件
const AlbumDetailWrapper = () => {
  const location = useLocation();
  
  // 详情页使用路径作为 key，确保不同专辑使用不同实例
  const getKey = () => {
    const path = location.pathname;
    if (path.startsWith('/album/')) {
      return `album-${path.split('/')[2]}`;
    }
    return 'album';
  };

  return <AlbumDetail key={getKey()} />;
};

// 需要登录的路由组件
const ProtectedRoute = ({ children }: { children: JSX.Element }) => {
  const { isAuthenticated, isLoading } = useUser()
  
  if (isLoading) {
    return <div className="min-h-screen flex items-center justify-center">加载中...</div>
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  return children
}

function App(): JSX.Element {
  return (
    <ThemeProvider>
      <OfflineProvider>
        <UserProvider>
          <Routes>
            {/* 公开路由 */}
            <Route path="/login" element={<Login />} />
            
            {/* 需要登录的路由 */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route index element={<HomeWrapper />} />
              <Route path="/org" element={<HomeWrapper />} />
              <Route path="/org/:id" element={<HomeWrapper />} />
              <Route path="/model" element={<HomeWrapper />} />
              <Route path="/model/:id" element={<HomeWrapper />} />
              <Route path="/cosplayer" element={<HomeWrapper />} />
              <Route path="/cosplayer/:id" element={<HomeWrapper />} />
              <Route path="/character" element={<HomeWrapper />} />
              <Route path="/character/:id" element={<HomeWrapper />} />
              <Route path="/tag/:id" element={<HomeWrapper />} />
              <Route path="/album/:id" element={<AlbumDetailWrapper />} />
              <Route path="/settings" element={<Settings />} />
            </Route>
          </Routes>
          <PWAInstallPrompt />
        </UserProvider>
      </OfflineProvider>
    </ThemeProvider>
  )
}

export default App