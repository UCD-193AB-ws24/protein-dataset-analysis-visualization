<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { API_BASE_URL } from '$lib/api';
	import { getTokens } from '$lib/getTokens';

	let userFileGroups = [];
	let errorMessage = '';
	let loading = false;
	let authenticated = false;

	onMount(async () => {
		try {
			await fetchUserFileGroups();
		} catch (error) {
			errorMessage = error.message || 'Failed to load data';
		}
	});

	async function fetchUserFileGroups() {
		loading = true;
		errorMessage = '';
		const {idToken, accessToken} = await getTokens();

		if (!idToken || !accessToken) {
			errorMessage = 'Missing authentication tokens. Please log in again.';
			loading = false;
			goto("/invalid-login")
			return;
		}
		authenticated = true;

		try {
			const response = await fetch(`${API_BASE_URL}/get_user_file_groups`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					Authorization: `Bearer ${accessToken}`,
					'X-ID-Token': idToken
				}
			});

			if (!response.ok) {
				throw new Error(`Error fetching file groups: ${response.statusText}`);
			}

			const data = await response.json();
			userFileGroups = data.file_groups;
		} catch (error) {
			errorMessage = error.message || 'An error occurred.';
		} finally {
			loading = false;
		}
	}
</script>
{#if authenticated}
<div class="file-groups">
	<h2>📁 Your File Groups</h2>

	{#if loading}
		<p>Loading file groups...</p>
	{/if}

	{#if errorMessage}
		<p class="error">{errorMessage}</p>
	{/if}

	{#if userFileGroups.length > 0}
		<div class="card-container">
			{#each userFileGroups as group}
				<div class="card">
					<h3>{group.title}</h3>
					<p>Description: {group.description}</p>
					<p>Genomes: {group.genomes.join(', ')}</p>
					<p>Num Genes: {group.num_genes}</p>
					<p>Num Domains: {group.num_domains}</p>
					<p>Domain Specific: {group.is_domain_specific ? 'Yes' : 'No'}</p>
					<p>Files:</p>
					{#if group.files.length > 0}
						<ul class="group-file-list">
							{#each group.files as file}
								{#if file.file_type !== 'graph'}
									<li style="word-wrap: break-word; overflow-wrap: break-word;">
										<strong>{`${file.file_type}`}</strong>{`: ${file.file_name}`}
									</li>
								{/if}
							{/each}
						</ul>
						<button on:click={() => goto(`/diagram?groupId=${group.id}`)}>
							View Diagram
						</button>
					{:else}
						<p class="no-files">No files included</p>
					{/if}
				</div>
			{/each}
		</div>
	{:else if !loading}
		<p>No file groups found.</p>
	{/if}
</div>
{/if}

<style>
	.file-groups {
		margin-top: 30px;
	}

	.card-container {
		display: grid;
		grid-template-columns: repeat(3, minmax(200px, 1fr));
		gap: 15px;
		margin-top: 15px;
	}

	.card {
		padding: 15px;
		background: #f9f9f9;
		border: 1px solid #ddd;
		border-radius: 8px;
		box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
		text-align: left;
	}

	.card h3 {
		margin: 0 0 10px;
		font-size: 18px;
		color: #333;
	}

	.card p {
		margin: 5px 0;
		font-size: 14px;
		color: #555;
	}

	.group-file-list {
		list-style-type: none;
		padding: 0;
		margin-top: 0px;
		font-size: 14px;
		color: #555;
		max-width: 100%;
	}

	.no-files {
		font-style: italic;
		color: #999;
	}

	.error {
		color: red;
		font-size: 14px;
	}
</style>
