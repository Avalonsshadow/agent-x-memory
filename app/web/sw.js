// Cache only public static shell, never private records, exports or API responses.
const CACHE='agent-x-shell-v4';
const ASSETS=['/','/style.css','/app.js','/manifest.webmanifest','/icon.svg'];
self.addEventListener('install',event=>{event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(ASSETS)));self.skipWaiting()});
self.addEventListener('activate',event=>event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k))))));
self.addEventListener('fetch',event=>{const url=new URL(event.request.url);if(event.request.method!=='GET'||url.origin!==self.location.origin||url.pathname.startsWith('/api/'))return;if(ASSETS.includes(url.pathname))event.respondWith(fetch(event.request).catch(()=>caches.match(event.request)))});
