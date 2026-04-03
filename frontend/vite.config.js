import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'happy-dom',
    setupFiles: ['./src/setupTests.js'],
    css: { modules: { classNameStrategy: 'non-scoped' } },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/accounts": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
})
