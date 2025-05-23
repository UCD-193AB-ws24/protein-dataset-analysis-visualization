<script lang="ts">
    import { onMount } from 'svelte';
    import { oidcClient, signOutRedirect } from '$lib/auth';
    import { page } from '$app/state';

    let isAuthenticated = false;
    let user: any = null;

    onMount(async () => {
        try {
            user = await oidcClient.getUser();
            isAuthenticated = user && !user.expired;
        } catch (error) {
            console.error('Error getting user:', error);
            isAuthenticated = false;
        }
    });

    $: isActive = (path: string) => page.url.pathname.includes(path) ? 'text-green-700 font-medium relative after:absolute after:bottom-[-8px] after:left-0 after:w-full after:h-0.5 after:bg-green-700' : 'text-slate-700 hover:text-green-600';

    function handleLogin() {
        oidcClient.signinRedirect();
    }

    async function handleLogout() {
        try {
            // First clear local state
            isAuthenticated = false;
            user = null;

            // Use the custom signOutRedirect function
            await signOutRedirect();
        } catch (error) {
            console.error('Logout error:', error);
        }
    }
</script>

<nav class="sticky top-0 z-10 bg-white shadow-sm">
    <div class="w-[95%] max-w-[1600px] mx-auto py-4">
        <div class="flex items-center justify-between">
            <!-- Left side -->
            <div class="flex items-center space-x-8">
                <a href="/" class="flex items-center">
                    <span class="text-xl font-bold text-green-700 leading-none">
                        LocusCGVT
                    </span>
                </a>
                <div class="hidden md:flex items-center space-x-6">
                    {#if isAuthenticated}
                        <a href="/dashboard" class={`${isActive('/dashboard')} text-sm leading-none py-2`}>
                            Dashboard
                        </a>
                    {/if}
                    <a href="/diagram" class={`${isActive('/diagram')} text-sm leading-none py-2`}>
                        Visualize
                    </a>
                    <a href="/about" class={`${isActive('/about')} text-sm leading-none py-2`}>
                        About
                    </a>
                </div>
            </div>
            <!-- Right side -->
            <div class="flex items-center space-x-4">
                <a href="/help" class={`${isActive('/help')} text-sm flex items-center gap-1 leading-none py-2`}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-help-circle"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/></svg>
                    <span class="hidden sm:inline">Help</span>
                </a>
                {#if isAuthenticated}
                    <button on:click={handleLogout} class="text-sm flex items-center gap-1 text-slate-700 hover:text-green-600 cursor-pointer leading-none py-2">
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-log-out"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
                        <span class="hidden sm:inline">Logout</span>
                    </button>
                {:else}
                    <button on:click={handleLogin} class="text-sm flex items-center gap-1 text-slate-700 hover:text-green-600 cursor-pointer leading-none py-2">
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-log-in"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><polyline points="10 17 15 12 10 7"/><line x1="15" y1="12" x2="3" y2="12"/></svg>
                        <span class="hidden sm:inline">Login</span>
                    </button>
                {/if}
            </div>
        </div>
    </div>
</nav>

<style>
    /* Add any additional styles here if needed */
</style>