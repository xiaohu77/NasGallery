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

  // 分类、列表API识别 - 网络优先
  const isDataAPIRequest = (
    // 生产环境域名
    (url.origin.includes('back.xiaohu777.cn') ||
     url.origin.includes('localhost') ||
     url.origin.includes('127.0.0.1')) &&
    // 数据API路径模式（排除详情页图片列表）
    (url.pathname.startsWith('/albums/') && !url.pathname.includes('/images') ||
     url.pathname.startsWith('/categories/') ||
     url.pathname.startsWith('/health') ||
     url.pathname === '/')
  );
  // 图片API识别 - 缓存优先
  const isImageAPIRequest = (
    // 生产环境域名
    (url.origin.includes('back.xiaohu777.cn') ||
     url.origin.includes('localhost') ||
     url.origin.includes('127.0.0.1')) &&
    // 图片API路径模式
    (url.pathname.startsWith('/covers/') ||
     (url.pathname.includes('/images/') && (url.pathname.endsWith('.jpg') || url.pathname.endsWith('.png') || url.pathname.endsWith('.jpeg'))))
  );
  

  if (isDataAPIRequest) {
    event.respondWith(handleDataAPIRequest(request));
    return;
  }
  
  // 详情页图片列表API识别 - 缓存优先
  const isAlbumImagesAPIRequest = (
    // 生产环境域名
    (url.origin.includes('back.xiaohu777.cn') ||
     url.origin.includes('localhost') ||
     url.origin.includes('127.0.0.1')) &&
    // 详情页图片列表API路径模式（精确匹配）
    url.pathname.match(/\/albums\/\d+\/images$/) !== null
  );
  

  if (isAlbumImagesAPIRequest) {
    event.respondWith(handleAlbumImagesAPIRequest(request));
    return;
  }
  
  if (isImageAPIRequest) {
    event.respondWith(handleImageAPIRequest(request));
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

// 处理数据API请求 - 网络优先策略
async function handleDataAPIRequest(request) {
  // 跳过 chrome-extension 协议的请求
  if (request.url.startsWith('chrome-extension://')) {
    return fetch(request);
  }
  
  try {
    // 1. 尝试网络请求
    const response = await fetch(request);
    
    // 2. 如果成功，缓存响应
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      const responseToCache = response.clone();
      // 添加时间戳到响应头
      const headers = new Headers(responseToCache.headers);
      headers.append('sw-cache-date', new Date().toISOString());
      const modifiedResponse = new Response(await responseToCache.clone().blob(), {
        status: responseToCache.status,
        statusText: responseToCache.statusText,
        headers: headers
      });
      await cache.put(request, modifiedResponse);
    }
    
    return response;
  } catch (error) {
    // 3. 网络失败，尝试从缓存返回
    const cachedResponse = await caches.match(request);
    
    if (cachedResponse) {
      // 检查缓存是否过期（5分钟）
      const cachedDate = cachedResponse.headers.get('sw-cache-date');
      if (cachedDate) {
        const cacheTime = new Date(cachedDate).getTime();
        const now = Date.now();
        
        if (now - cacheTime < API_CACHE_DURATION) {
          return cachedResponse; // 返回有效缓存
        }
      } else {
        return cachedResponse; // 无时间戳，直接返回
      }
    }
    
    // 4. 缓存也不存在，返回离线响应
    // 返回一个空的JSON响应，让前端可以正常处理
    const offlineResponse = new Response(JSON.stringify({
      items: [],
      page: 1,
      size: 20,
      total: 0
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });
    return offlineResponse;
  }
}

// 处理详情页图片列表API请求 - 缓存优先策略
async function handleAlbumImagesAPIRequest(request) {
  // 跳过 chrome-extension 协议的请求
  if (request.url.startsWith('chrome-extension://')) {
    return fetch(request);
  }
  
  try {
    // 1. 首先尝试从缓存获取
    const cachedResponse = await caches.match(request);
    
    if (cachedResponse) {
      // 2. 检查缓存是否过期（图片列表缓存时间适中，1天）
      const cachedDate = cachedResponse.headers.get('sw-cache-date');
      if (cachedDate) {
        const cacheTime = new Date(cachedDate).getTime();
        const now = Date.now();
        const ALBUM_IMAGES_CACHE_DURATION = 24 * 60 * 60 * 1000; // 1天
        
        if (now - cacheTime < ALBUM_IMAGES_CACHE_DURATION) {
          return cachedResponse; // 返回有效缓存
        }
      } else {
        return cachedResponse; // 无时间戳，直接返回
      }
    }
    
    // 3. 缓存中没有，尝试网络获取
    const response = await fetch(request);
    
    // 4. 如果成功，缓存响应
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      const responseToCache = response.clone();
      // 添加时间戳到响应头
      const headers = new Headers(responseToCache.headers);
      headers.append('sw-cache-date', new Date().toISOString());
      const modifiedResponse = new Response(await responseToCache.clone().blob(), {
        status: responseToCache.status,
        statusText: responseToCache.statusText,
        headers: headers
      });
      await cache.put(request, modifiedResponse);
    }
    
    return response;
  } catch (error) {
    // 5. 网络和缓存都失败，返回错误
    throw error;
  }
}

// 处理图片API请求 - 缓存优先策略
async function handleImageAPIRequest(request) {
  // 跳过 chrome-extension 协议的请求
  if (request.url.startsWith('chrome-extension://')) {
    return fetch(request);
  }
  
  try {
    // 1. 首先尝试从缓存获取
    const cachedResponse = await caches.match(request);
    
    if (cachedResponse) {
      // 2. 检查缓存是否过期（图片缓存时间更长，30天）
      const cachedDate = cachedResponse.headers.get('sw-cache-date');
      if (cachedDate) {
        const cacheTime = new Date(cachedDate).getTime();
        const now = Date.now();
        const IMAGE_CACHE_DURATION = 30 * 24 * 60 * 60 * 1000; // 30天
        
        if (now - cacheTime < IMAGE_CACHE_DURATION) {
          return cachedResponse; // 返回有效缓存
        }
      } else {
        return cachedResponse; // 无时间戳，直接返回
      }
    }
    
    // 3. 缓存中没有，尝试网络获取
    const response = await fetch(request);
    
    // 4. 如果成功，缓存响应
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      const responseToCache = response.clone();
      // 添加时间戳到响应头
      const headers = new Headers(responseToCache.headers);
      headers.append('sw-cache-date', new Date().toISOString());
      const modifiedResponse = new Response(await responseToCache.clone().blob(), {
        status: responseToCache.status,
        statusText: responseToCache.statusText,
        headers: headers
      });
      await cache.put(request, modifiedResponse);
    }
    
    return response;
  } catch (error) {
    // 5. 网络和缓存都失败，返回错误
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



// 监听来自页面的消息
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
