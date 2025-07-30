// Đặt tên cho bộ nhớ cache
const CACHE_NAME = 'qr-manager-v1';

// Danh sách các tệp cần lưu vào cache để chạy offline
const urlsToCache = [
  './', // Trang chủ
  './index.html', // Tệp HTML chính
  './icons/icon-192x192.png',
  './icons/icon-512x512.png',
  'https://cdn.jsdelivr.net/npm/qrcode@1.5.0/build/qrcode.min.js',
  'https://cdn.sheetjs.com/xlsx-0.20.0/package/dist/xlsx.full.min.js'
];

// Sự kiện 'install': Xảy ra khi Service Worker được cài đặt
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

// Sự kiện 'fetch': Xảy ra mỗi khi có một yêu cầu mạng từ ứng dụng
// Chiến lược: Cache first - Ưu tiên lấy từ cache, nếu không có mới lấy từ mạng
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Nếu tìm thấy trong cache, trả về ngay lập tức
        if (response) {
          return response;
        }
        // Nếu không, thực hiện yêu cầu mạng thực sự
        return fetch(event.request);
      }
    )
  );
});