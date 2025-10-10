import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: false,
    proxy: {
      // optional dev proxy if API runs on 8005 and you want same-origin during dev
      '/api': {
        target: 'http://localhost:8005',
        changeOrigin: true
      }
    }
  }
});
