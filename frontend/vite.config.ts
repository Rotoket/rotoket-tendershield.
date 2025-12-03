import path from 'path';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  server: {
    port: 5173, // Стандартный порт Vite
    host: true,
  },
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    }
  },
  // @ts-ignore - vitest config
  test: {
    environment: 'jsdom',
    globals: true,
  },
});
