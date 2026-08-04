const CACHE_NAME = "study-planner-cache-v3";
const OFFLINE_URL = "/static/offline.html";
const OFFLINE_URLS = [
  OFFLINE_URL,
  "/static/css/style.css",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(OFFLINE_URLS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

// Network-first for pages (so logged-in data is always fresh). If the
// network is unavailable for a page navigation, fall back to the cached
// offline page instead of the browser's default error screen. Static
// assets fall back to cache when offline too.
self.addEventListener("fetch", (event) => {
  const { request } = event;

  if (request.method !== "GET") return;

  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request).catch(() => caches.match(OFFLINE_URL))
    );
    return;
  }

  if (OFFLINE_URLS.some((url) => request.url.includes(url))) {
    event.respondWith(
      caches.match(request).then((cached) => cached || fetch(request))
    );
  }
});

// --------------------------------------------------------------------
// Push Notifications — foundation only. This correctly displays a push
// message IF one arrives, but nothing currently sends one: that needs a
// VAPID key pair + a subscribe endpoint storing subscriptions server-side
// + a trigger (e.g. a reminder due today). Wire that up before relying on
// this in production; until then it's inert, not broken.
// --------------------------------------------------------------------
self.addEventListener("push", (event) => {
  const data = event.data ? event.data.json() : {};
  const title = data.title || "Student Study Planner";
  const options = {
    body: data.body || "You have something due — open the app to check.",
    icon: "/static/icons/icon-192.png",
    badge: "/static/icons/icon-96.png",
    data: { url: data.url || "/dashboard" },
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) || "/dashboard";
  event.waitUntil(clients.openWindow(url));
});

// --------------------------------------------------------------------
// Background Sync — foundation only. Registers correctly when the app
// calls sw.sync.register("retry-failed-writes"), but there's no offline
// write queue (IndexedDB) feeding it yet, so it has nothing to replay.
// Real offline-first task/note creation needs that queue built next.
// --------------------------------------------------------------------
self.addEventListener("sync", (event) => {
  if (event.tag === "retry-failed-writes") {
    event.waitUntil(Promise.resolve());
  }
});

self.addEventListener("periodicsync", (event) => {
  if (event.tag === "refresh-reminders") {
    event.waitUntil(Promise.resolve());
  }
});
