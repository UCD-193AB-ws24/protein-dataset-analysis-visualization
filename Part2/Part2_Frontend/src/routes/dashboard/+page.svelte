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
		created_at: string;
		last_updated_at: string;
	}

	const sortOptions = [
		{ label: 'Last Updated (Most Recent)', value: 'updated-desc' },
		{ label: 'Last Updated (Least Recent)', value: 'updated-asc' },
		{ label: 'Date Created (Newest)', value: 'created-desc' },
		{ label: 'Date Created (Oldest)', value: 'created-asc' }
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
	let sortBy = 'updated-desc';
	let filterBy = 'all';
	let deletingGroupId: string | null = null;

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

	async function fetchUserFileGroups() {
		loading = true;
		errorMessage = '';

		if (!user?.access_token) {
			errorMessage = 'Missing authentication tokens. Please log in again.';
			loading = false;
			goto("/invalid-login");
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
				throw new Error(`Error fetching projects: ${response.statusText}`);
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
		if (!confirm('Are you sure you want to delete this file group? This action cannot be undone.')) {
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
			userFileGroups = userFileGroups.filter(group => group.id !== groupId);
			filteredFileGroups = filteredFileGroups.filter(group => group.id !== groupId);
		} catch (error) {
			errorMessage = error instanceof Error ? error.message : 'Failed to delete group';
		} finally {
			deletingGroupId = null;
		}
	}

	$: {
		// Apply filters and search
		filteredFileGroups = userFileGroups.filter(group => {
			const matchesSearch = searchQuery === '' ||
				group.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
				group.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
				group.genomes.some(genome => genome.toLowerCase().includes(searchQuery.toLowerCase()));

			const matchesFilter = filterBy === 'all' ||
				(filterBy === 'domain' && group.is_domain_specific) ||
				(filterBy === 'general' && !group.is_domain_specific);

			return matchesSearch && matchesFilter;
		});

		// Apply sorting
		if (sortBy) {
			filteredFileGroups.sort((a, b) => {
				const isDescending = sortBy.endsWith('desc');
				const isUpdatedSort = sortBy.startsWith('updated');

				// Primary sort by the main timestamp
				const primaryA = new Date(isUpdatedSort ? a.last_updated_at : a.created_at).getTime();
				const primaryB = new Date(isUpdatedSort ? b.last_updated_at : b.created_at).getTime();

				if (primaryA !== primaryB) {
					return isDescending ? primaryB - primaryA : primaryA - primaryB;
				}

				// Secondary sort by the other timestamp
				const secondaryA = new Date(isUpdatedSort ? a.created_at : a.last_updated_at).getTime();
				const secondaryB = new Date(isUpdatedSort ? b.created_at : b.last_updated_at).getTime();

				return isDescending ? secondaryB - secondaryA : secondaryA - secondaryB;
			});
		}
	}
</script>

{#if isAuthenticated}
<div class="w-[95%] max-w-[1600px] mx-auto py-8">
	<div class="mb-8 flex items-start justify-between">
		<div>
			<h1 class="text-3xl font-bold text-slate-800 mb-2">Your Projects</h1>
			<p class="text-slate-600">Manage and analyze your protein sequence comparisons</p>
		</div>
		<a
			href="/diagram"
			class="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors duration-200 cursor-pointer"
		>
			<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mr-2">
				<path d="M12 5v14M5 12h14"/>
			</svg>
			Create New Diagram
		</a>
	</div>

	<div class="flex flex-col md:flex-row gap-4 mb-6">
		<div class="md:w-1/3 flex items-end">
			<div class="relative w-full">
				<input
					type="text"
					bind:value={searchQuery}
					placeholder="Search projects..."
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
					<circle cx="11" cy="11" r="8"/>
					<path d="m21 21-4.3-4.3"/>
				</svg>
			</div>
		</div>
		<div class="flex gap-4 md:ml-auto">
			<div class="w-48">
				<label for="sort-select" class="block text-xs font-medium text-slate-700 mb-1">Sort by:</label>
				<select
					id="sort-select"
					bind:value={sortBy}
					class="w-full px-4 py-2 bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
				>
					{#each sortOptions as option}
						<option value={option.value}>{option.label}</option>
					{/each}
				</select>
			</div>
			<div class="w-48">
				<label for="filter-select" class="block text-xs font-medium text-slate-700 mb-1">Filter by:</label>
				<select
					id="filter-select"
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

	{#if !loading && filteredFileGroups.length >= 0}
		<div class="mb-4">
			<p class="text-sm text-slate-600">
				Showing {filteredFileGroups.length} of {userFileGroups.length} project{userFileGroups.length !== 1 ? 's' : ''}
				{#if searchQuery || filterBy !== 'all'}
					{#if searchQuery && filterBy !== 'all'}
						for "{searchQuery}" in {filterOptions.find(f => f.value === filterBy)?.label.toLowerCase()}
					{:else if searchQuery}
						for "{searchQuery}"
					{:else if filterBy !== 'all'}
						in {filterOptions.find(f => f.value === filterBy)?.label.toLowerCase()}
					{/if}
				{/if}
			</p>
		</div>
	{/if}

	{#if loading}
		<div class="flex justify-center items-center py-8">
			<div class="animate-spin rounded-full h-12 w-12 border-4 border-green-200"></div>
			<div class="animate-spin rounded-full h-12 w-12 border-4 border-green-600 border-t-transparent absolute"></div>
		</div>
	{/if}

	{#if errorMessage}
		<p class="text-red-600 bg-red-50 p-4 rounded-lg mb-4">{errorMessage}</p>
	{/if}

	{#if filteredFileGroups.length > 0}
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
			{#each filteredFileGroups as group}
				<div class="bg-white rounded-lg shadow-sm border border-slate-200 p-4 hover:shadow-md transition-shadow flex flex-col h-full">
					<div class="flex-1">
						<div class="flex items-start justify-between mb-2">
							<div class="flex items-center">
								<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-slate-400 mr-2">
									<circle cx="6" cy="8" r="2"/>
									<circle cx="18" cy="8" r="2"/>
									<circle cx="6" cy="16" r="2"/>
									<circle cx="18" cy="16" r="2"/>
									<line x1="6" y1="8" x2="18" y2="8"/>
									<line x1="6" y1="16" x2="18" y2="16"/>
									<line x1="6" y1="8" x2="18" y2="16"/>
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
							<p>Created: {new Date(group.created_at).toLocaleString()}</p>
							<p>Last Updated: {new Date(group.last_updated_at).toLocaleString()}</p>
						</div>
					</div>
					<div class="mt-4 flex items-center justify-between">
						<span class={`text-xs px-2 py-1 rounded-full ${group.is_domain_specific ? 'bg-blue-100 text-blue-700' : 'bg-green-100 text-green-700'}`}>
							{group.is_domain_specific ? 'Domain-specific' : 'General'}
						</span>

						<div class="flex gap-2">
							<button
								on:click={() => deleteGroup(group.id)}
								disabled={deletingGroupId === group.id}
								class="inline-flex items-center px-3 py-1.5 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors duration-200 cursor-pointer disabled:bg-red-300 disabled:cursor-not-allowed"
							>
								{deletingGroupId === group.id ? 'Deleting...' : 'Delete'}
							</button>
							<button
								on:click={() => goto(`/diagram?groupId=${group.id}`)}
								class="inline-flex items-center px-3 py-1.5 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors duration-200 cursor-pointer"
							>
								View Diagram
								<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="ml-1">
									<path d="M5 12h14"/>
									<path d="m12 5 7 7-7 7"/>
								</svg>
							</button>
						</div>
					</div>
				</div>
			{/each}
		</div>
	{:else if !loading}
		<div class="text-center py-8">
			<p class="text-slate-600">No projects found.</p>
		</div>
	{/if}
</div>
{/if}

<style>
	/* Empty style tag required for Tailwind processing */
</style>
