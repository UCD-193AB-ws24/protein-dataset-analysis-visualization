<script lang="ts">
	import { oidcClient } from '$lib/auth';

	function startLogin() {
		oidcClient.signinRedirect();
	}
</script>

<h1>Sign in to your account</h1>

<button on:click={startLogin}>Sign in with AWS</button>
