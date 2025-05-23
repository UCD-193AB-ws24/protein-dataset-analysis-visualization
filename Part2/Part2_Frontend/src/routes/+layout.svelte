<script>
    import '../app.css';
    import Navbar from '../lib/components/Navbar.svelte';
</script>

<div class="min-h-screen bg-gray-100 flex flex-col">
    <Navbar />
    <main class="flex-1 relative">
        <slot />
    </main>
</div>

<style>
    /* Empty style tag required for Tailwind processing */
</style>

