<script lang="ts">
	import { onMount } from 'svelte';
	import { oidcClient } from '$lib/auth';
	import { API_BASE_URL } from '$lib/envs';

	onMount(async () => {
		try {
			const user = await oidcClient.signinRedirectCallback();

			if (!user?.access_token || !user?.id_token) {
				throw new Error('Missing authentication tokens');
			}

			// ✅ Call backend to verify user and register if new
			const res = await fetch(`${API_BASE_URL}/verify_user`, {
				method: 'GET',
				headers: {
					Authorization: `Bearer ${user.access_token}`,
					'X-ID-Token': user.id_token
				}
			});

			if (!res.ok) {
				console.error('User verification failed:', await res.text());
				window.location.href = '/invalid-login';
				return;
			}

			const data = await res.json();
			console.log('Verified user:', data);

			window.location.href = '/dashboard';
		} catch (e) {
			console.error('Auth callback error:', e);
			window.location.href = '/invalid-login';
		}
	});
</script>

<div class="w-[95%] max-w-[1600px] mx-auto py-8">
    <div class="max-w-3xl mx-auto text-center">
        <div class="bg-white p-8 rounded-lg shadow-md">
            <div class="flex flex-col items-center gap-4">
                <div class="relative">
                    <div class="animate-spin rounded-full h-16 w-16 border-4 border-green-200"></div>
                    <div class="animate-spin rounded-full h-16 w-16 border-4 border-green-600 border-t-transparent absolute top-0 left-0"></div>
                </div>
                <h2 class="text-xl font-semibold text-slate-800">Verifying your login...</h2>
                <p class="text-slate-600">Please wait while we complete the authentication process.</p>
            </div>
        </div>
    </div>
</div>

<style>
    /* Empty style tag required for Tailwind processing */
</style>
