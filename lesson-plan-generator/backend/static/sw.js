const CACHE_NAME = 'cbc-lesson-cache-v1';
const urlsToCache = [
  '/',
  '/static/js/script.js',
  '/static/css/style.css',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png'
];

// Install event - cache files
self.addEventListener('install', (event) => {
  console.log('Service Worker installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
      .then(() => self.skipWaiting())
  );
});

// Activate event - cleanup old caches
self.addEventListener('activate', (event) => {
  console.log('Service Worker activating...');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.filter(name => name !== CACHE_NAME)
                  .map(name => caches.delete(name))
      );
    })
  );
});

// Fetch event - serve from cache if offline
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
          .then(response => response || fetch(event.request))
          .catch(() => caches.match('/')) // fallback to home page
  );
});
