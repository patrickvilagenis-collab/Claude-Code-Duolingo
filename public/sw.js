// Service worker mínimo para offline básico (PWA).
// Cache-first para el app shell; network-first para el contenido (lecciones)
// para que las actualizaciones por PR se reflejen sin borrar caché.
const CACHE = 'ccd-v1'
const SHELL = ['./', './index.html', './manifest.webmanifest']

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()))
})

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim()),
  )
})

self.addEventListener('fetch', (e) => {
  const { request } = e
  if (request.method !== 'GET') return
  const url = new URL(request.url)

  // Contenido de lecciones: red primero, caché como respaldo.
  if (url.pathname.includes('/content/')) {
    e.respondWith(
      fetch(request).then((res) => {
        const copy = res.clone()
        caches.open(CACHE).then((c) => c.put(request, copy))
        return res
      }).catch(() => caches.match(request)),
    )
    return
  }

  // Resto: caché primero, red como respaldo.
  e.respondWith(caches.match(request).then((hit) => hit || fetch(request)))
})
