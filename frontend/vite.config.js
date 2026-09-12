import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      '/video_feed': { target: 'http://127.0.0.1:5000', changeOrigin: true },
      '/test_frame': { target: 'http://127.0.0.1:5000', changeOrigin: true },
      '/process_frame': { target: 'http://127.0.0.1:5000', changeOrigin: true },
      '/latest':     { target: 'http://127.0.0.1:5000', changeOrigin: true },
      '/set_mode':   { target: 'http://127.0.0.1:5000', changeOrigin: true },
      '/static':     { target: 'http://127.0.0.1:5000', changeOrigin: true }
    }
  }
})
