import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

const backendUrl = process.env.BACKEND_URL ?? 'http://localhost:8000'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    allowedHosts: true,
    proxy: {
      '/api': backendUrl,
      '/setup/': backendUrl,
      '/auth': backendUrl,
      '/mcp': backendUrl,
    },
  },
})
