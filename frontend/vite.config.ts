import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    // Allow all hosts so Ngrok or Cloudflare Tunnels can connect safely
    allowedHosts: true,
    // Proxy /api requests to the local Python backend
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
});
