import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'
import { registerServiceWorker } from './utils/pwa'
import { PWAService } from './services/pwaService'

// 注册Service Worker
if ('serviceWorker' in navigator) {
  registerServiceWorker()
  
  // 预加载数据（延迟执行，避免影响首屏加载）
  setTimeout(() => {
    const pwaService = new PWAService()
    // 预加载分类树和第一页图集
    Promise.all([
      pwaService.getCategoryTree(),
      pwaService.getAlbums(1, 20)
    ]).catch(() => {
      // 预加载失败不影响用户体验
    })
  }, 3000)
}

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
)

root.render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
)