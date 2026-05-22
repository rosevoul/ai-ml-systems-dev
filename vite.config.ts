import { defineConfig } from 'vite'

// ← Set this to your GitHub repo name, e.g. '/faye-recsys/'
const REPO_NAME = '/ai-ml-systems-dev/'

export default defineConfig({
  base: process.env.NODE_ENV === 'production' ? REPO_NAME : '/',
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    rollupOptions: {
      output: {
        manualChunks: { d3: ['d3'] }
      }
    }
  }
})
