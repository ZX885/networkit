import react from '@vitejs/plugin-react';
import { defineConfig, loadEnv } from 'vite';

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // DEV_API_TARGET — адрес Django для dev-прокси (frontend/.env.development, см. .env.development.example).
  // По умолчанию NetworkIt локально запускается на порту 8100: python manage.py runserver 8100
  const env = loadEnv(mode, process.cwd(), '');
  const apiTarget = env.DEV_API_TARGET || 'http://127.0.0.1:8100';

  return {
    plugins: [react()],
    server: {
      // Порт не меняем: на 5173 завязаны SITE_URL (ссылки в письмах) и CSRF_TRUSTED_ORIGINS.
      // Если порт занят, Vite должен остановиться с ошибкой, а не переехать на другой.
      port: 5173,
      strictPort: true,
      // Запросы /api/... идут на Django. changeOrigin не задаём: заголовки Host и Origin остаются
      // от Vite (localhost:5173), и проверка CSRF в Django видит совпадающий адрес.
      proxy: {
        '/api': { target: apiTarget },
      },
    },
  };
});
