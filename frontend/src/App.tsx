import { Routes, Route, useLocation } from 'react-router-dom'
import { ThemeProvider } from './contexts/ThemeContext'
import { OfflineProvider } from './contexts/OfflineContext'
import Layout from './components/Layout'
import PWAInstallPrompt from './components/PWAInstallPrompt'
import Home from './pages/Home'
import AlbumDetail from './pages/AlbumDetail'

// 创建一个包装组件来管理 Home 页面的 key
const HomeWrapper = () => {
  const location = useLocation();
  
  // 为不同路径的 Home 组件生成不同的 key
  // 这样可以确保不同分类的列表页使用不同的组件实例
  // 但同一分类下，从详情页返回时不会重新挂载
  const getKey = () => {
    const path = location.pathname;
    if (path === '/') return 'home-all';
    if (path.startsWith('/org/')) return `home-org`;
    if (path.startsWith('/model/')) return `home-model`;
    if (path.startsWith('/tag/')) return `home-tag`;
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

function App(): JSX.Element {
  return (
    <ThemeProvider>
      <OfflineProvider>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<HomeWrapper />} />
            <Route path="/org/:id" element={<HomeWrapper />} />
            <Route path="/model/:id" element={<HomeWrapper />} />
            <Route path="/tag/:id" element={<HomeWrapper />} />
            <Route path="/album/:id" element={<AlbumDetailWrapper />} />
          </Route>
        </Routes>
        <PWAInstallPrompt />
      </OfflineProvider>
    </ThemeProvider>
  )
}

export default App