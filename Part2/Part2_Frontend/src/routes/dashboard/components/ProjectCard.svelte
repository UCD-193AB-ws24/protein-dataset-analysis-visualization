<script>
    import { goto } from '$app/navigation';

    export let group;
    export let deleteGroup;
    export let deletingGroupId;
</script>

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


<style>

</style>