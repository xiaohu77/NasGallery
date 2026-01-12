// Service Worker 版本号
const CACHE_VERSION = 'v1.0.0';
const CACHE_NAME = `girlatlas-${CACHE_VERSION}`;

// 需要缓存的核心资源
const CORE_CACHE_FILES = [
  '/',
  '/index.html',
  '/manifest.json',
  '/icon-192.png',
  '/icon-512.png'
];

// API缓存策略
const API_CACHE_DURATION = 5 * 60 * 1000; // 5分钟

// 安装事件 - 缓存核心资源
self.addEventListener('install', (event) => {
  self.skipWaiting(); // 立即激活新版本
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(CORE_CACHE_FILES);
    })
  );
});

// 激活事件 - 清理旧缓存
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME && cacheName.startsWith('girlatlas-')) {
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      return self.clients.claim();
    })
  );
});

// 拦截请求事件
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // 跳过非GET请求
  if (request.method !== 'GET') {
    return;
  }

  // 跳过 chrome-extension 协议的请求
  if (request.url.startsWith('chrome-extension://')) {
    return;
  }

  // API请求处理 - 识别所有API端点
  const isAPIRequest = (
    // 生产环境域名
    url.origin.includes('back.xiaohu777.cn') ||
    // 开发环境域名
    url.origin.includes('localhost') ||
    url.origin.includes('127.0.0.1') ||
    // API路径模式（兼容旧代码）
    url.pathname.startsWith('/api/') ||
    // 实际使用的路径模式（不以/api开头）
    url.pathname.startsWith('/albums/') ||
    url.pathname.startsWith('/categories/') ||
    url.pathname.startsWith('/covers/') ||
    url.pathname.startsWith('/health') ||
    url.pathname === '/'
  );
  
  if (isAPIRequest) {
    event.respondWith(handleAPIRequest(request));
    return;
  }

  // 静态资源处理
  if (
    url.origin === self.location.origin ||
    request.destination === 'document' ||
    request.destination === 'style' ||
    request.destination === 'script' ||
    request.destination === 'font'
  ) {
    event.respondWith(handleStaticRequest(request));
    return;
  }
});

// 处理API请求
async function handleAPIRequest(request) {
  // 跳过 chrome-extension 协议的请求
  if (request.url.startsWith('chrome-extension://')) {
    return fetch(request);
  }
  
  try {
    // 尝试网络请求
    const response = await fetch(request);
    
    // 如果成功，缓存响应
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      // 使用Request对象作为缓存键，而不是字符串
      const responseToCache = response.clone();
      await cache.put(request, responseToCache);
    }
    
    return response;
  } catch (error) {
    // 网络失败，尝试从缓存返回
    const cachedResponse = await caches.match(request);
    
    if (cachedResponse) {
      // 检查缓存是否过期
      const cachedDate = cachedResponse.headers.get('sw-cache-date');
      if (cachedDate) {
        const cacheTime = new Date(cachedDate).getTime();
        const now = Date.now();
        
        if (now - cacheTime < API_CACHE_DURATION) {
          return cachedResponse;
        }
      } else {
        return cachedResponse;
      }
    }
    
    // 缓存也不存在，返回错误
    throw error;
  }
}

// 处理静态资源请求
async function handleStaticRequest(request) {
  // 跳过 chrome-extension 协议的请求
  if (request.url.startsWith('chrome-extension://')) {
    return fetch(request);
  }
  
  // 首先尝试从缓存获取
  const cachedResponse = await caches.match(request);
  
  if (cachedResponse) {
    return cachedResponse;
  }
  
  // 如果缓存中没有，尝试网络获取
  try {
    const response = await fetch(request);
    
    // 如果成功，缓存响应（排除 chrome-extension）
    if (response.ok &&
        !request.url.startsWith('chrome-extension://') &&
        (request.destination === 'style' || request.destination === 'script' || request.destination === 'image' || request.destination === 'font')) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    
    return response;
  } catch (error) {
    // 网络失败，返回离线页面或默认响应
    if (request.destination === 'document') {
      return caches.match('/index.html');
    }
    throw error;
  }
}

// 后台同步事件
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-albums') {
    event.waitUntil(syncAlbumsData());
  }
});

// 后台同步数据
async function syncAlbumsData() {
  try {
    const cache = await caches.open(CACHE_NAME);
    // 使用正确的API路径（不以/api开头）
    const request = new Request('/albums/?page=1&size=20');
    
    // 跳过 chrome-extension 协议的请求
    if (request.url.startsWith('chrome-extension://')) {
      return;
    }
    
    const response = await fetch(request);
    if (response.ok) {
      // 添加时间戳到响应头
      const headers = new Headers(response.headers);
      headers.append('sw-cache-date', new Date().toISOString());
      const modifiedResponse = new Response(await response.clone().blob(), {
        status: response.status,
        statusText: response.statusText,
        headers: headers
      });
      await cache.put(request, modifiedResponse);
    }
  } catch (error) {
    console.log('后台同步失败:', error);
  }
}

// 监听来自页面的消息
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});