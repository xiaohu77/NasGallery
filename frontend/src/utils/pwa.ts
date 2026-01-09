/**
 * PWA 工具函数
 * 提供Service Worker注册、离线状态管理等功能
 */

// 注册Service Worker
export const registerServiceWorker = async (): Promise<void> => {
  if (!('serviceWorker' in navigator)) {
    console.log('Service Worker 不支持');
    return;
  }

  try {
    const registration = await navigator.serviceWorker.register('/sw.js');
    console.log('Service Worker 注册成功:', registration);

    // 监听Service Worker更新
    registration.addEventListener('updatefound', () => {
      const newWorker = registration.installing;
      if (newWorker) {
        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            // 有新版本可用
            showUpdateNotification();
          }
        });
      }
    });

    // 监听控制器变化
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      window.location.reload();
    });
  } catch (error) {
    console.log('Service Worker 注册失败:', error);
  }
};

// 注销Service Worker
export const unregisterServiceWorker = async (): Promise<void> => {
  if (!('serviceWorker' in navigator)) return;

  try {
    const registration = await navigator.serviceWorker.getRegistration();
    if (registration) {
      await registration.unregister();
      console.log('Service Worker 注销成功');
    }
  } catch (error) {
    console.log('Service Worker 注销失败:', error);
  }
};

// 显示更新通知
const showUpdateNotification = (): void => {
  // 创建自定义通知
  const notification = document.createElement('div');
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: #3b82f6;
    color: white;
    padding: 16px 20px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    z-index: 10000;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    display: flex;
    align-items: center;
    gap: 12px;
    animation: slideIn 0.3s ease-out;
  `;
  
  notification.innerHTML = `
    <span>📦 发现新版本</span>
    <button id="update-btn" style="
      background: white;
      color: #3b82f6;
      border: none;
      padding: 6px 12px;
      border-radius: 4px;
      cursor: pointer;
      font-weight: 600;
      font-size: 14px;
    ">刷新</button>
    <button id="close-btn" style="
      background: transparent;
      color: white;
      border: 1px solid white;
      padding: 6px 12px;
      border-radius: 4px;
      cursor: pointer;
      font-size: 14px;
    ">稍后</button>
  `;

  // 添加动画样式
  const style = document.createElement('style');
  style.textContent = `
    @keyframes slideIn {
      from { transform: translateX(100%); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }
  `;
  document.head.appendChild(style);

  document.body.appendChild(notification);

  // 绑定按钮事件
  const updateBtn = notification.querySelector('#update-btn');
  const closeBtn = notification.querySelector('#close-btn');

  updateBtn?.addEventListener('click', () => {
    if (navigator.serviceWorker.controller) {
      navigator.serviceWorker.controller.postMessage({ type: 'SKIP_WAITING' });
    }
    notification.remove();
  });

  closeBtn?.addEventListener('click', () => {
    notification.remove();
  });
};

// 检查网络状态
export const checkNetworkStatus = (): boolean => {
  return navigator.onLine;
};

// 监听网络状态变化
export const listenToNetworkChanges = (callback: (isOnline: boolean) => void): void => {
  window.addEventListener('online', () => callback(true));
  window.addEventListener('offline', () => callback(false));
};