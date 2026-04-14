import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '');
  const backendUrl = env.BACKEND_URL || 'http://127.0.0.1:3001';
  const devPort = parseInt(env.VITE_PORT || '3000', 10);
  const devHost = env.VITE_HOST || '0.0.0.0';
  return {
    server: {
      port: devPort,
      host: devHost,
      allowedHosts: ['all'],
      proxy: {
        '/api': {
          target: backendUrl,
          changeOrigin: true,
        },
        '/audio': {
          target: backendUrl,
          changeOrigin: true,
        },
        '/editor': {
          target: backendUrl,
          changeOrigin: true,
        },
        '/blog': {
          target: backendUrl,
          changeOrigin: true,
        },
      },
    },
    optimizeDeps: {
      exclude: ['@ffmpeg/ffmpeg', '@ffmpeg/util'],
    },
    plugins: [react()],
    define: {
      'process.env.API_KEY': JSON.stringify(env.GEMINI_API_KEY),
      'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY)
    },
    resolve: {
      alias: {
        '@': path.resolve(__dirname, '.'),
      }
    }
  };
});
