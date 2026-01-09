import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    open: false
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    // PWA相关构建配置
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          // 将较大的依赖分开打包
        }
      }
    }
  },
  // 静态资源处理
  publicDir: 'public'
})