import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5000,
    strictPort: true,
    cors: true,
    allowedHosts: [
      '85352116-0f67-429a-b43b-e82b9b4c08c4-00-yey2ngmhi2dx.sisko.replit.dev',
      '.replit.dev',
      '.repl.co',
      '.sisko.replit.dev'
    ],
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
