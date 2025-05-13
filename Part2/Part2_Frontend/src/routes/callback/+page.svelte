<script lang="ts">
	import { onMount } from 'svelte';
	import { oidcClient } from '$lib/auth';

	onMount(async () => {
		try {
			const user = await oidcClient.signinRedirectCallback();

			const idToken = user.id_token;
			const accessToken = user.access_token;

			localStorage.setItem('id_token', idToken);
			localStorage.setItem('access_token', accessToken);
			localStorage.setItem('email', user.profile.email);

			// ✅ Call backend to verify user and register if new
			const res = await fetch('http://localhost:3050/verify_user', {
				method: 'GET',
				headers: {
					Authorization: `Bearer ${accessToken}`,
					'X-ID-Token': idToken
				}
			});

			if (!res.ok) {
				console.error('User verification failed:', await res.text());
				window.location.href = '/invalid-login';
				return;
			}

			const data = await res.json();
			console.log('Verified user:', data);

			window.location.href = '/dashboard/files';
		} catch (e) {
			console.error('Auth callback error:', e);
			window.location.href = '/invalid-login';
		}
	});
</script>

<p>Verifying login...</p>
