import fs from 'node:fs'
import path from 'node:path'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

function spaFallback() {
  return {
    name: 'spa-fallback',
    closeBundle() {
      const index = path.resolve('dist/index.html')
      if (fs.existsSync(index)) {
        fs.copyFileSync(index, path.resolve('dist/404.html'))
      }
    },
  }
}

export default defineConfig({
  plugins: [react(), spaFallback()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/media': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
})
