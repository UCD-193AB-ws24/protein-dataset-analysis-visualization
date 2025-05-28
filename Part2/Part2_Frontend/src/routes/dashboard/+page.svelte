<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { API_BASE_URL } from '$lib/envs';
	import { oidcClient } from '$lib/auth';

	interface File {
		file_name: string;
		file_type: string;
	}

	interface FileGroup {
		id: string;
		title: string;
		description: string;
		genomes: string[];
		num_genes: number;
		num_domains: number;
		is_domain_specific: boolean;
		files: File[];
	}

	const sortOptions = [
		{ label: 'Not functional', value: 'not-functional' }
		// { label: 'Date Uploaded (Newest)', value: 'uploaded-desc' },
		// { label: 'Date Uploaded (Oldest)', value: 'uploaded-asc' },
		// { label: 'Date Modified (Newest)', value: 'modified-desc' },
		// { label: 'Date Modified (Oldest)', value: 'modified-asc' }
	];

	const filterOptions = [
		{ label: 'All Types', value: 'all' },
		{ label: 'General', value: 'general' },
		{ label: 'Domain-specific', value: 'domain' }
	];

	let userFileGroups: FileGroup[] = [];
	let filteredFileGroups: FileGroup[] = [];
	let errorMessage = '';
	let loading = true;
	let isAuthenticated = false;
	let user: any = null;
	let searchQuery = '';
	let sortBy = '';
	let filterBy = 'all';
	let deletingGroupId: string | null = null;

	let sharingGroupId: string | null = null;
	let recipientEmailMap: Record<string, string> = {};

	onMount(async () => {
		try {
			user = await oidcClient.getUser();
			isAuthenticated = user && !user.expired;

			if (isAuthenticated) {
				await fetchUserFileGroups();
			} else {
				goto('/invalid-login');
			}
		} catch (error) {
			console.error('Auth error:', error);
			goto('/invalid-login');
		}
	});

	async function sendShare(groupId: string) {
		const email = recipientEmailMap[groupId];
		if (!email) {
			alert('Please enter a valid email.');
			return;
		}

		const formData = new FormData();
		formData.append('reciever_email', email);
		formData.append('group_id', groupId);

		try {
			const response = await fetch(`${API_BASE_URL}/post_inbox`, {
				method: 'POST',
				headers: {
					Authorization: `Bearer ${user.access_token}`
				},
				body: formData
			});

			if (!response.ok) {
				const data = await response.json();
				throw new Error(data.error || 'Failed to share');
			}

			alert('Group shared successfully!');
			sharingGroupId = null;
		} catch (error) {
			alert(error instanceof Error ? error.message : 'Failed to share');
		}
	}

	async function fetchUserFileGroups() {
		loading = true;
		errorMessage = '';

		if (!user?.access_token) {
			errorMessage = 'Missing authentication tokens. Please log in again.';
			loading = false;
			goto('/invalid-login');
			return;
		}

		try {
			const response = await fetch(`${API_BASE_URL}/get_user_file_groups`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					Authorization: `Bearer ${user.access_token}`,
					'X-ID-Token': user.id_token
				}
			});

			if (!response.ok) {
				throw new Error(`Error fetching file groups: ${response.statusText}`);
			}

			const data = await response.json();
			userFileGroups = data.file_groups;
			filteredFileGroups = [...userFileGroups];
		} catch (error) {
			errorMessage = error instanceof Error ? error.message : 'An error occurred.';
		} finally {
			loading = false;
		}
	}

	async function deleteGroup(groupId: string) {
		if (
			!confirm('Are you sure you want to delete this file group? This action cannot be undone.')
		) {
			return;
		}

		deletingGroupId = groupId;
		errorMessage = '';

		try {
			const response = await fetch(`${API_BASE_URL}/delete_group?groupId=${groupId}`, {
				method: 'DELETE',
				headers: {
					Authorization: `Bearer ${user.access_token}`
				}
			});

			if (!response.ok) {
				throw new Error(`Error deleting group: ${response.statusText}`);
			}

			// Remove the deleted group from both lists
			userFileGroups = userFileGroups.filter((group) => group.id !== groupId);
			filteredFileGroups = filteredFileGroups.filter((group) => group.id !== groupId);
		} catch (error) {
			errorMessage = error instanceof Error ? error.message : 'Failed to delete group';
		} finally {
			deletingGroupId = null;
		}
	}

	$: {
		// Apply filters and search
		filteredFileGroups = userFileGroups.filter((group) => {
			const matchesSearch =
				searchQuery === '' ||
				group.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
				group.description.toLowerCase().includes(searchQuery.toLowerCase());

			const matchesFilter =
				filterBy === 'all' ||
				(filterBy === 'domain' && group.is_domain_specific) ||
				(filterBy === 'general' && !group.is_domain_specific);

			return matchesSearch && matchesFilter;
		});

		// Apply sorting
		if (sortBy) {
			filteredFileGroups.sort((a, b) => {
				// Add sorting logic based on sortBy value
				// For now, just return 0 to maintain current order
				return 0;
			});
		}
	}
</script>

{#if isAuthenticated}
	<div class="w-[95%] max-w-[1600px] mx-auto py-8">
		<div class="mb-8">
			<h1 class="text-3xl font-bold text-slate-800 mb-2">Your Uploads</h1>
			<p class="text-slate-600">Manage and analyze your protein sequence comparisons</p>
		</div>

		<div class="flex flex-col md:flex-row gap-4 mb-6">
			<div class="md:w-1/3">
				<div class="relative">
					<input
						type="text"
						bind:value={searchQuery}
						placeholder="Search groups..."
						class="w-full pl-10 pr-4 py-2 bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
					/>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="20"
						height="20"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						stroke-linecap="round"
						stroke-linejoin="round"
						class="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400"
					>
						<circle cx="11" cy="11" r="8" />
						<path d="m21 21-4.3-4.3" />
					</svg>
				</div>
			</div>
			<div class="flex gap-4 md:ml-auto">
				<div class="w-48">
					<select
						bind:value={sortBy}
						class="w-full px-4 py-2 bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
					>
						<option value="">Sort by</option>
						{#each sortOptions as option}
							<option value={option.value}>{option.label}</option>
						{/each}
					</select>
				</div>
				<div class="w-48">
					<select
						bind:value={filterBy}
						class="w-full px-4 py-2 bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
					>
						{#each filterOptions as option}
							<option value={option.value}>{option.label}</option>
						{/each}
					</select>
				</div>
			</div>
		</div>

		{#if loading}
			<div class="flex justify-center items-center py-8">
				<div class="animate-spin rounded-full h-12 w-12 border-4 border-green-200"></div>
				<div
					class="animate-spin rounded-full h-12 w-12 border-4 border-green-600 border-t-transparent absolute"
				></div>
			</div>
		{/if}

		{#if errorMessage}
			<p class="text-red-600 bg-red-50 p-4 rounded-lg mb-4">{errorMessage}</p>
		{/if}

		{#if filteredFileGroups.length > 0}
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
				{#each filteredFileGroups as group}
					<div
						class="bg-white rounded-lg shadow-sm border border-slate-200 p-4 hover:shadow-md transition-shadow"
					>
						<div class="flex items-start justify-between mb-2">
							<div class="flex items-center">
								<svg
									xmlns="http://www.w3.org/2000/svg"
									width="20"
									height="20"
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									stroke-width="2"
									stroke-linecap="round"
									stroke-linejoin="round"
									class="text-slate-400 mr-2"
								>
									<circle cx="6" cy="8" r="2" />
									<circle cx="18" cy="8" r="2" />
									<circle cx="6" cy="16" r="2" />
									<circle cx="18" cy="16" r="2" />
									<line x1="6" y1="8" x2="18" y2="8" />
									<line x1="6" y1="16" x2="18" y2="16" />
									<line x1="6" y1="8" x2="18" y2="16" />
								</svg>
								<h3 class="font-medium text-slate-800">{group.title}</h3>
							</div>
						</div>
						<div class="mb-3">
							<p class="text-sm text-slate-600 line-clamp-2">{group.description}</p>
						</div>
						<div class="space-y-2 text-sm text-slate-600">
							<p>Genomes: {group.genomes.join(', ')}</p>
							<p>Num Genes: {group.num_genes}</p>
							<p>Num Domains: {group.num_domains}</p>
						</div>
						<div class="mt-4 flex items-center justify-between">
							{#if sharingGroupId === group.id}
								<!-- Inline sharing input -->
								<div class="flex gap-2 items-center w-full mt-3">
									<input
										type="email"
										bind:value={recipientEmailMap[group.id]}
										placeholder="Enter recipient email"
										class="flex-grow px-3 py-1.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
									/>
									<!-- Send button -->
									<button
										on:click={() => sendShare(group.id)}
										class="p-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors flex items-center justify-center"
										aria-label="Send group to recipient"
									>
										<svg
											xmlns="http://www.w3.org/2000/svg"
											class="w-5 h-5"
											fill="none"
											viewBox="0 0 24 24"
											stroke="currentColor"
											stroke-width="2"
											stroke-linecap="round"
											stroke-linejoin="round"
										>
											<line x1="22" y1="2" x2="11" y2="13" />
											<polygon points="22 2 15 22 11 13 2 9 22 2" />
										</svg>
									</button>

									<!-- Cancel button -->
									<button
										on:click={() => (sharingGroupId = null)}
										class="p-2 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded-lg flex items-center justify-center"
										aria-label="Cancel sharing"
									>
										<svg
											xmlns="http://www.w3.org/2000/svg"
											class="w-5 h-5"
											fill="none"
											viewBox="0 0 24 24"
											stroke="currentColor"
											stroke-width="2"
											stroke-linecap="round"
											stroke-linejoin="round"
										>
											<line x1="18" y1="6" x2="6" y2="18" />
											<line x1="6" y1="6" x2="18" y2="18" />
										</svg>
									</button>
								</div>
							{:else}
								<!-- Normal button set -->
								<span
									class={`text-xs px-2 py-1 rounded-full ${group.is_domain_specific ? 'bg-blue-100 text-blue-700' : 'bg-green-100 text-green-700'}`}
								>
									{group.is_domain_specific ? 'Domain-specific' : 'General'}
								</span>
								<div class="flex gap-2 mt-3">
									<button
										on:click={() => (sharingGroupId = group.id)}
										class="inline-flex items-center px-3 py-1.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
									>
										Share
									</button>
									<button
										on:click={() => deleteGroup(group.id)}
										class="inline-flex items-center px-3 py-1.5 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700"
										disabled={deletingGroupId === group.id}
									>
										{deletingGroupId === group.id ? 'Deleting...' : 'Delete'}
									</button>
									<button
										on:click={() => goto(`/diagram?groupId=${group.id}`)}
										class="inline-flex items-center px-3 py-1.5 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700"
									>
										View Diagram
									</button>
								</div>
							{/if}
						</div>
					</div>
				{/each}
			</div>
		{:else if !loading}
			<div class="text-center py-8">
				<p class="text-slate-600">No file groups found.</p>
			</div>
		{/if}
	</div>
{/if}

<style>
	/* Empty style tag required for Tailwind processing */
</style>
