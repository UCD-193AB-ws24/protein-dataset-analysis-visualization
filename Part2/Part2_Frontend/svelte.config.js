import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';
import path from 'path';

export default {
  preprocess: vitePreprocess(),
  kit: {
    adapter: adapter({
      fallback: 'index.html' // fallback HTML for unmatched routes
    }),
    paths: {
      base: ''
    },
    alias: {
      $lib: path.resolve('./src/lib'),
    }
  }
};
