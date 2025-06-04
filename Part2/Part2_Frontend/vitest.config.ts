import { defineConfig } from 'vitest/config';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  plugins: [svelte()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.test.{js,ts}', 'src/**/*.spec.{js,ts}'],
    exclude: ['src/lib/test/test_files/**', 'node_modules/**'],
    deps: {
      inline: [/svelte/]
    },
    environmentOptions: {
      jsdom: {
        resources: 'usable'
      }
    },
    browser: {
      enabled: true,
      headless: true,
      provider: 'playwright',
      name: 'chromium'
    }
  },
}); 