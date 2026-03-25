/**
 * 画宗 Service Worker — PWA 离线缓存
 *
 * 策略：
 * 1. App Shell（HTML/CSS/JS）：Cache First — 快速启动
 * 2. API 数据：Network First — 保证最新，离线时用缓存
 * 3. 静态资源（图片/字体）：Cache First — 减少带宽
 * 4. 缩略图/预览：Stale While Revalidate — 显示缓存 + 后台更新
 */

const CACHE_VERSION = 'huazong-v1'
const STATIC_CACHE = `${CACHE_VERSION}-static`
const API_CACHE = `${CACHE_VERSION}-api`
const IMAGE_CACHE = `${CACHE_VERSION}-images`

// App Shell 必须缓存的资源
const APP_SHELL = [
  '/',
  '/index.html',
  '/manifest.json',
  '/favicon.ico'
]

// 安装：预缓存 App Shell
self.addEventListener('install', (event) => {
  console.log('[SW] 安装中...')
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  )
})

// 激活：清理旧缓存
self.addEventListener('activate', (event) => {
  console.log('[SW] 激活中...')
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key.startsWith('huazong-') && key !== STATIC_CACHE && key !== API_CACHE && key !== IMAGE_CACHE)
          .map((key) => {
            console.log('[SW] 删除旧缓存:', key)
            return caches.delete(key)
          })
      )
    ).then(() => self.clients.claim())
  )
})

// 请求拦截
self.addEventListener('fetch', (event) => {
  const { request } = event
  const url = new URL(request.url)

  // 只处理 GET 请求
  if (request.method !== 'GET') return

  // 跳过 WebSocket 和 Chrome 扩展
  if (url.protocol === 'ws:' || url.protocol === 'wss:' ||
      url.protocol === 'chrome-extension:') return

  // API 请求：Network First
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirst(request, API_CACHE))
    return
  }

  // 图片和缩略图：Cache First
  if (isImageRequest(url)) {
    event.respondWith(cacheFirst(request, IMAGE_CACHE))
    return
  }

  // JS/CSS bundle（带 hash 的）：Cache First
  if (isHashedAsset(url)) {
    event.respondWith(cacheFirst(request, STATIC_CACHE))
    return
  }

  // HTML 页面：Network First（SPA 路由）
  if (request.headers.get('accept')?.includes('text/html')) {
    event.respondWith(networkFirst(request, STATIC_CACHE))
    return
  }

  // 其他静态资源：Cache First
  event.respondWith(cacheFirst(request, STATIC_CACHE))
})

// ---- 缓存策略 ----

async function cacheFirst(request, cacheName) {
  const cached = await caches.match(request)
  if (cached) return cached

  try {
    const response = await fetch(request)
    if (response.ok) {
      const cache = await caches.open(cacheName)
      cache.put(request, response.clone())
    }
    return response
  } catch {
    return offlineFallback()
  }
}

async function networkFirst(request, cacheName) {
  try {
    const response = await fetch(request)
    if (response.ok) {
      const cache = await caches.open(cacheName)
      cache.put(request, response.clone())
    }
    return response
  } catch {
    const cached = await caches.match(request)
    if (cached) return cached
    return offlineFallback()
  }
}

function offlineFallback() {
  return new Response(
    `<!DOCTYPE html>
    <html lang="zh-CN">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>画宗 — 离线</title>
      <style>
        body {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
          display: flex;
          align-items: center;
          justify-content: center;
          min-height: 100vh;
          margin: 0;
          background: #1a1a2e;
          color: #fff;
          text-align: center;
        }
        .offline-box { max-width: 400px; padding: 2rem; }
        h1 { font-size: 1.5rem; margin-bottom: 0.5rem; }
        p { color: #aaa; font-size: 0.9rem; }
        button {
          margin-top: 1rem;
          padding: 0.6rem 1.5rem;
          background: #e94560;
          color: #fff;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          font-size: 0.9rem;
        }
      </style>
    </head>
    <body>
      <div class="offline-box">
        <h1>📡 网络连接已断开</h1>
        <p>当前无法连接服务器，已缓存的内容仍可查看。</p>
        <button onclick="location.reload()">重试连接</button>
      </div>
    </body>
    </html>`,
    { headers: { 'Content-Type': 'text/html; charset=utf-8' } }
  )
}

// ---- 工具函数 ----

function isImageRequest(url) {
  return /\.(png|jpg|jpeg|gif|webp|svg|ico)$/i.test(url.pathname) ||
    url.pathname.includes('/pictures/thumbnails/') ||
    url.pathname.includes('/pictures/originals/')
}

function isHashedAsset(url) {
  // Vite/Webpack 带 hash 的文件名，如 app.a1b2c3d4.js
  return /\.[a-f0-9]{8,}\.(js|css)$/i.test(url.pathname) ||
    url.pathname.includes('/assets/')
}

// ---- 推送通知 ----

self.addEventListener('push', (event) => {
  if (!event.data) return

  let data
  try {
    data = event.data.json()
  } catch {
    data = { title: '画宗通知', body: event.data.text() }
  }

  event.waitUntil(
    self.registration.showNotification(data.title || '画宗通知', {
      body: data.body || '',
      icon: '/android-chrome-192x192.png',
      badge: '/favicon-32x32.png',
      tag: data.tag || 'huazong-notification',
      data: data.url ? { url: data.url } : undefined
    })
  )
})

self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  const url = event.notification.data?.url || '/'

  event.waitUntil(
    self.clients.matchAll({ type: 'window' }).then((clients) => {
      // 如果已有窗口，聚焦并导航
      for (const client of clients) {
        if (client.url === url && 'focus' in client) {
          return client.focus()
        }
      }
      // 否则打开新窗口
      return self.clients.openWindow(url)
    })
  )
})
