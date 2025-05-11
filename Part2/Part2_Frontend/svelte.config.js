import adapter from '@sveltejs/adapter-node';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';
import path from 'path';

export default {
  preprocess: vitePreprocess(),
  kit: {
    adapter: adapter(), // ✅ switch to Node adapter for SSR
    alias: {
      $lib: path.resolve('./src/lib')
    }
  }
};
