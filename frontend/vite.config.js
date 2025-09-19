import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // IMPORTANT: make assets absolute at /static/
  base: '/static/',
  build: {
    outDir: 'dist',        // will produce frontend/dist
    emptyOutDir: true,
    assetsDir: 'assets'
  }
})

