import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import nodePolyfills from 'rollup-plugin-node-polyfills';

export default defineConfig({
	plugins: [sveltekit()],
	optimizeDeps: {
		include: ['buffer', 'process']
	},
	define: {
		global: 'globalThis' // 👈 makes 'global' available in browser
	},
	build: {
		rollupOptions: {
			plugins: [nodePolyfills()] // 👈 polyfills Node modules like buffer/process
		}
	}
});
