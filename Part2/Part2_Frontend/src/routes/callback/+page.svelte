<script lang="ts">
	import { onMount } from 'svelte';
	import { userManager, signOutRedirect } from '$lib/auth/userManager';
	import { API_BASE_URL } from '$lib/api';

	let email = '';
	let accessToken = '';
	let idToken = '';
	let refreshToken = '';

	onMount(async () => {
		try {
			const user = await userManager.signinRedirectCallback();

			email = user.profile?.email ?? '';
			accessToken = user.access_token;
			idToken = user.id_token;
			refreshToken = user.refresh_token;

			// Optional: redirect to home or dashboard
			// window.location.href = '/';
			console.log('sending token:', accessToken);
			const response = await fetch(`${API_BASE_URL}/api/user-data`, {
				method: 'GET',
				headers: { Authorization: `Bearer ${accessToken}`,
					'X-ID-Token': idToken,
				 }
			});

			const data = await response.json();
			if (!response.ok) {
				console.error('auth failed:', data.error);
				return;
			}

			console.log('user id:', data.user.id);
			console.log('user email:', data.user.email);
			console.log('server returned:', data);
		} catch (err) {
			console.error('Signin callback failed', err);
		}
	});
	async function handleSignOut() {
		await signOutRedirect();
	}
</script>

<div>
	<p>Hello: {email}</p>
	<p>Access token: {accessToken}</p>
	<p>ID token: {idToken}</p>
	<p>Refresh token: {refreshToken}</p>
	<button on:click={handleSignOut}>Log out</button>
</div>
