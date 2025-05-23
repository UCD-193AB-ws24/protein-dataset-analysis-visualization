<script>
    import { oidcClient } from '$lib/auth';

    function handleLogin() {
        oidcClient.signinRedirect();
    }
</script>

<div class="w-[95%] max-w-[1600px] mx-auto py-8">
    <div class="max-w-3xl mx-auto text-center">
        <div class="bg-red-50 p-8 rounded-lg shadow-md">
            <h1 class="text-4xl font-bold text-red-600 mb-4">🔒 Access Denied</h1>
            <p class="text-lg text-slate-600 mb-6">You must be logged in to access this page.</p>
            <div class="flex flex-col sm:flex-row items-center justify-center gap-4">
                <button
                    on:click={handleLogin}
                    class="inline-flex items-center px-6 py-3 text-base font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors duration-200 shadow-md hover:shadow-lg cursor-pointer"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mr-2"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><polyline points="10 17 15 12 10 7"/><line x1="15" y1="12" x2="3" y2="12"/></svg>
                    Login
                </button>
                <a
                    href="/"
                    class="inline-flex items-center px-6 py-3 text-base font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors duration-200 shadow-md hover:shadow-lg"
                >
                    Return to Homepage
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="ml-2"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
                </a>
            </div>
        </div>
    </div>
</div>

<style>
    /* Empty style tag required for Tailwind processing */
</style>
