import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

const nm = path.resolve(__dirname, 'node_modules')

export default defineConfig({
  plugins: [react()],
  server: {
    fs: { allow: [path.resolve(__dirname, '..')] },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
      '@testing-library/react': path.join(nm, '@testing-library/react'),
      '@testing-library/jest-dom': path.join(nm, '@testing-library/jest-dom'),
      '@testing-library/user-event': path.join(nm, '@testing-library/user-event'),
      'react': path.join(nm, 'react'),
      'react-dom': path.join(nm, 'react-dom'),
      'react/jsx-runtime': path.join(nm, 'react/jsx-runtime'),
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    include: ['../tests/web/**/*.test.tsx', '../tests/web/**/*.test.ts'],
    setupFiles: ['./vitest.setup.ts'],
  },
})
