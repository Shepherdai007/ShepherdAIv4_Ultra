const CACHE_NAME = 'shepherd-ai-ultra-v4';
const ASSETS = [
    '/',
    '/static/style.css', // In case you move CSS later
    '/static/manifest.json',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
];

// 1. Install Event - Caching the Shell
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('ShepherdAI Ultra: Caching Shell Assets');
            return cache.addAll(ASSETS);
        })
    );
    self.skipWaiting();
});

// 2. Activate Event - Cleaning up old v3 versions
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.filter(key => key !== CACHE_NAME)
                    .map(key => caches.delete(key))
            );
        })
    );
    self.clients.claim();
});

// 3. Fetch Event - "Network First" for Search, "Cache First" for Icons
self.addEventListener('fetch', (event) => {
    // We don't want to cache API calls (Chat/Search/Tavily)
    if (event.request.url.includes('/chat') || event.request.url.includes('/upload')) {
        return; 
    }

    event.respondWith(
        caches.match(event.request).then((response) => {
            // Return from cache if found, otherwise hit the network
            return response || fetch(event.request).then((fetchRes) => {
                return caches.open(CACHE_NAME).then((cache) => {
                    // Only cache internal static files, not external APIs
                    if (event.request.url.startsWith(self.location.origin)) {
                        cache.put(event.request.url, fetchRes.clone());
                    }
                    return fetchRes;
                });
            });
        }).catch(() => {
            // Fallback: If offline and looking for index, return cached home
            if (event.request.mode === 'navigate') {
                return caches.match('/');
            }
        })
    );
});