import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Запросы /api/... идут на Django. changeOrigin не задаём: заголовки Host и Origin остаются
    // от Vite (localhost:5173), и проверка CSRF в Django видит совпадающий адрес.
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000' },
    },
  },
});
