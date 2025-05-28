<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { API_BASE_URL } from '$lib/envs';
	import { oidcClient } from '$lib/auth';

	interface InboxMessage {
		id: string;
		sender: string;
		group_id: string;
	}

	let user: any = null;
	let isAuthenticated = false;
	let loading = true;
	let errorMessage = '';
	let inboxMessages: InboxMessage[] = [];

	onMount(async () => {
		try {
			user = await oidcClient.getUser();
			isAuthenticated = user && !user.expired;

			if (!isAuthenticated) {
				goto('/invalid-login');
				return;
			}

			await fetchInbox();
		} catch (error) {
			console.error('Auth error:', error);
			goto('/invalid-login');
		}
	});

	async function fetchInbox() {
		loading = true;
		errorMessage = '';

		try {
			const response = await fetch(`${API_BASE_URL}/get_messages?token=${user.access_token}`, {
				method: 'GET'
			});

			if (!response.ok) {
				throw new Error(`Failed to load inbox: ${response.statusText}`);
			}

			const data = await response.json();
			inboxMessages = data.Messages;
		} catch (error) {
			errorMessage = error instanceof Error ? error.message : 'An error occurred.';
		} finally {
			loading = false;
		}
	}
</script>

{#if isAuthenticated}
	<div class="w-[95%] max-w-[1000px] mx-auto py-8">
		<div class="mb-8">
			<h1 class="text-3xl font-bold text-slate-800 mb-2">Inbox</h1>
			<p class="text-slate-600">Shared groups sent to you by others</p>
		</div>

		{#if loading}
			<div class="flex justify-center items-center py-8">
				<div class="animate-spin rounded-full h-12 w-12 border-4 border-green-200"></div>
				<div class="animate-spin rounded-full h-12 w-12 border-4 border-green-600 border-t-transparent absolute"></div>
			</div>
		{:else if errorMessage}
			<p class="text-red-600 bg-red-50 p-4 rounded-lg mb-4">{errorMessage}</p>
		{:else if inboxMessages.length === 0}
			<div class="text-center py-8">
				<p class="text-slate-600">Your inbox is empty. No one has shared any groups with you yet.</p>
			</div>
		{:else}
			<div class="space-y-4">
				{#each inboxMessages as msg}
					<div class="bg-white border border-slate-200 rounded-lg shadow-sm p-4 flex justify-between items-center">
						<div>
							<p class="text-slate-800 font-medium">Shared by: {msg.sender}</p>
							<p class="text-slate-600 text-sm">Group ID: <code>{msg.group_id}</code></p>
						</div>
						<div class="flex gap-2">
							<a
								href={`/diagram?groupId=${msg.group_id}`}
								class="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors"
							>
								View Group
							</a>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>
{/if}

<style>
	/* Empty style tag for Tailwind processing */
</style>
