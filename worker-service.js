/**
 * service-worker.js (y worker-service.js)
 * Service Worker completo para ejecución 100% sin Internet (Offline-First),
 * almacenamiento en caché de recursos locales y sincronización de datos JSON/CSV.
 */

const CACHE_NAME = 'deskdata-pro-local-v2.1.0';
const OFFLINE_ASSETS = [
  './',
  './index.html',
  './styles.css',
  './app.js',
  './manifest.json',
  './datos/registros.json',
  './datos/catalogo_inicial.csv',
  './icons/icon-192.png',
  './icons/icon-512.png'
];

// Instalación: guarda en caché local todos los archivos de la aplicación
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(OFFLINE_ASSETS);
    }).then(() => self.skipWaiting())
  );
});

// Activación: limpia versiones antiguas de caché local
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Estrategia Cache-First con actualización en segundo plano para funcionar sin Internet
self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;

  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(event.request)
        .then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const responseClone = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(event.request, responseClone);
            });
          }
          return networkResponse;
        })
        .catch(() => {
          if (event.request.mode === 'navigate') {
            return caches.match('./index.html');
          }
          return new Response(
            JSON.stringify({ offline: true, message: 'Recurso servido en modo local offline' }),
            { headers: { 'Content-Type': 'application/json' } }
          );
        });
    })
  );
});

// Comunicación bidireccional con la interfaz para tareas del Worker (respaldos, diagnóstico y actualización local)
self.addEventListener('message', (event) => {
  const data = event.data || {};
  if (data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  } else if (data.type === 'PING_WORKER') {
    if (event.source) {
      event.source.postMessage({
        type: 'WORKER_STATUS',
        status: 'ACTIVO (Offline Cache Ready)',
        cacheName: CACHE_NAME,
        timestamp: new Date().toLocaleTimeString()
      });
    }
  }
});
