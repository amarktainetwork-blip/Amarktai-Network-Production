import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// Vite configuration for the AmarkTai Network frontend.
// This file defines the aliases used throughout the project and
// specifies that the built files should be emitted to the `build` directory.
// The alias '@' points to the project source directory, mirroring the
// behaviour of the previous CRA configuration, and enabling imports like
// `import something from '@/lib/utils'` to resolve correctly.

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    outDir: 'build',
    emptyOutDir: true,
  },
});