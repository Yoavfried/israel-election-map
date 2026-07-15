import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    sourcemap: true,
    // MapLibre is intentionally isolated behind React.lazy; its minified chunk is about 1.03 MB.
    chunkSizeWarningLimit: 1_100,
  },
  server: {
    port: 4173,
    strictPort: true,
  },
})
