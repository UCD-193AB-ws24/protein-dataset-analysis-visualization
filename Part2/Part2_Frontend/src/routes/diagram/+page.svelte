<script lang="ts">
  import Chart from '$lib/Chart.svelte';
  import { onMount } from 'svelte';
  import { API_BASE_URL } from '$lib/envs';
  import { goto } from '$app/navigation';
  import { oidcClient } from '$lib/auth'
  import { getTokens } from '$lib/getTokens';
  import UploadModal from '$lib/components/UploadModal.svelte';

  interface Node {
    id: string;
    genome_name: string;
    protein_name: string;
    direction: string;   // "plus" | "minus"
    rel_position: number;
    is_present: boolean;
    gene_type?: string;
    _dup?: boolean;      // internal flag for duplicated bottom‑row copy
  }

  interface Link {
    source: string;
    target: string;
    score: number;       // 55‑100
    is_reciprocal: boolean;
  }

  interface Graph {
    domain_name?: string; // optional domain name
    nodes: Node[];
    links: Link[];
    genomes: string[];   // list of genome names
  }

  let groupId: string | null = null;    // Group ID for file retrieval
  let user: any = null;
  let isAuthenticated = false;

  let graphs: Graph[] = [];
  let selectedGraph: Graph = { nodes: [], links: [], genomes: [] }; // Current graph to be displayed
  let selectedGenomes: string[] = [];
  let filteredGraph: Graph = { nodes: [], links: [], genomes: [] };
  let draggedGenome: string | null = null;

  // Variables for uploaded files/inputs
  let uploadedCoordsFile: File | null = null;
  let uploadedMatrixFiles: File[] = [];
  let isDomainSpecific = false;

  // Variables for downloaded files
  let matrixFiles: { url: string; original_name: string }[] = [];
  let coordinateFile: { url: string; original_name: string } | null = null;

  let errorMessage = "";
  let loading = true;        // Loading state for file upload
  let savingGroup = false;   // Loading state for saving group
  let cutoff = 55;           // slider value

  // Link filter states
  let showReciprocal = true;
  let showNonReciprocal = true;
  let showConsistent = true;
  let showInconsistent = true;
  let showPartiallyConsistent = true;

  // Form information if user choses to save graph
  let title = '';
  let description = '';
  let numGenes = 0;
  let numDomains = 1;

  let showUploadModal = false;

  let isPanelCollapsed = false;

  let chartComponent: Chart;

  onMount(async () => {
    try {
      user = await oidcClient.getUser();
      isAuthenticated = user && !user.expired;

      const urlParams = new URLSearchParams(window.location.search);
      const initialId = urlParams.get('groupId');

      if (initialId) {
        groupId = initialId;
        await fetchGroupData(groupId);
      }

      loading = false;
    } catch (error) {
      console.error('Auth error:', error);
      goto('/invalid-login');
    }
  });

  function normaliseGraphs(data: any): Graph[] {
    // backend might return {graphs:[…]} (new) or {graph:{…}} (legacy)
    if (Array.isArray(data?.graphs)) return data.graphs;
    if (data?.graph) return [data.graph];
    // direct object passed
    if (Array.isArray(data)) return data;
    if (data?.nodes) return [data as Graph];
    throw new Error('No graph data found');
  }

  function chooseInitialGraph(graphs: Graph[]) {
    if (!Array.isArray(graphs)) {
      console.error("Expected 'graphs' to be an array, but got:", graphs);
      return { nodes: [], links: [], genomes: [] }; // Return an empty graph as fallback
    }
    return graphs.find(g => g.domain_name === 'ALL') || graphs[0];
  }

  async function fetchGroupData(id: string) {
    try {
      const response = await fetch(`${API_BASE_URL}/get_group_graph?groupId=${id}`);

      if (!response.ok) {
        throw new Error(`Error fetching graph: ${response.statusText}`);
      }

      const data = await response.json();
      console.log(data)
      graphs = normaliseGraphs(data.graphs);
      selectedGraph = chooseInitialGraph(graphs);

      numGenes = data.num_genes;
      numDomains = data.num_domains;
      title = data.title || '';
      description = data.description || '';

      // Set file data for download
      matrixFiles = data.matrix_files || [];
      coordinateFile = data.coordinate_file || null;

      // Reset selected genomes and filtered graph
      selectedGenomes = [];
      filteredGraph = { nodes: [], links: [], genomes: [] };
    } catch (error) {
      errorMessage = error instanceof Error ? error.message : "An error occurred.";
      console.error("Detailed error:", error);
    }
  }

  // Function to handle file uploads
  async function uploadFiles() {
    errorMessage = ""; // Clear any previous error messages
    if (!uploadedCoordsFile || uploadedMatrixFiles.length === 0) {
      throw new Error('Please select the required files.');
    }
    if (!isDomainSpecific && uploadedMatrixFiles.length !== 1) {
      throw new Error('Exactly one matrix file is required for non-domain-specific graphs.');
    }
    if (isDomainSpecific && uploadedMatrixFiles.length > 3) {
      throw new Error('Up to three matrix files are supported for domain-specific graphs.');
    }

    const formData = new FormData();
    formData.append('file_coordinate', uploadedCoordsFile);
    uploadedMatrixFiles.forEach((file, index) => formData.append(`file_matrix_${index}`, file));
    formData.append('is_domain_specific', isDomainSpecific ? 'true' : 'false');

    try {
      const response = await fetch(`${API_BASE_URL}/generate_graph`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `Upload failed: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('Fetched data:', data);
      graphs = normaliseGraphs(data.graphs);
      selectedGraph = chooseInitialGraph(graphs);
      numGenes = data.num_genes;
      numDomains = data.num_domains;
      isDomainSpecific = data.is_domain_specific || false;

      // Reset selected genomes and filtered graph
      selectedGenomes = [];
      filteredGraph = { nodes: [], links: [], genomes: [] };
      loading = false;
    } catch (error) {
      if (error instanceof TypeError && error.message === 'Failed to fetch') {
        throw new Error('Network error: Unable to connect to the server. Please check your internet connection.');
      }
      throw error;
    }
  }

  // Function to save the group of files
  async function saveGroup() {
    if (!title) {
      alert('Please provide a title for the group of files.');
      return;
    }

    if (!isAuthenticated) {
      alert('Please log in to save groups.');
      return;
    }

    savingGroup = true;
    const formData = new FormData();
    if (!groupId) {
      // For new groups, validate uploaded files
      if (!uploadedCoordsFile || uploadedMatrixFiles.length === 0) {
        alert('Please select at least one coordinate file and one matrix file to save.');
        savingGroup = false;
        return;
      }

      formData.append('file_coordinate', uploadedCoordsFile);
      uploadedMatrixFiles.forEach((file, index) => formData.append(`file_matrix_${index}`, file));
    } else {
      formData.append('group_id', groupId);
    }
    formData.append('title', title);
    formData.append('description', description);
    formData.append('num_genes', numGenes.toString());
    formData.append('num_domains', numDomains.toString());
    formData.append('is_domain_specific', isDomainSpecific ? 'true' : 'false');
    formData.append('genomes', JSON.stringify(selectedGraph.genomes));
    formData.append('graphs', JSON.stringify(graphs));

    try {
      const response = await fetch(`${API_BASE_URL}/save`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${user.access_token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const errorResponse = await response.json();
        const errorMessage = errorResponse.error || 'Unknown error';
        console.error('Error saving group:', errorMessage);
        throw new Error(`Failed to save group: ${response.statusText}`);
      }

      const result = await response.json();
      console.log('Group saved successfully:', result);
      alert('Group updated successfully!');

      if (!groupId) {
        // Transition to the view with the new groupId
        const newGroupId = result.group_id;
        groupId = newGroupId; // Update groupId in the component state
        await fetchGroupData(newGroupId); // Fetch the new group data
        goto(`?groupId=${newGroupId}`);
      }
    } catch (error) {
      console.error('Error saving group:', error);
      alert('Failed to save group. Please try again.');
    } finally {
      savingGroup = false;
    }
  }

  // Allow user to select up to 3 genomes
  function toggleGenomeSelection(genome: string) {
    if (selectedGenomes.includes(genome)) {
      selectedGenomes = selectedGenomes.filter(g => g !== genome);
    } else {
      selectedGenomes = [...selectedGenomes, genome];
    }
  }

  // Filter graph according to selected genomes
  function filterGraph() {
    if (selectedGenomes.length !== 3 && selectedGenomes.length !== 2) {
      console.error('Please select exactly 2 or 3 genomes to filter the graph.');
      return;
    }

    // Update genomes in filtered graph
    filteredGraph.genomes = selectedGenomes;
    filteredGraph.domain_name = selectedGraph.domain_name;  // Copy domain_name

    // Update nodes in filtered graph
    filteredGraph.nodes = selectedGraph.nodes.filter(node =>
      selectedGenomes.includes(node.genome_name)
    );

    // Update links in filtered graph
    filteredGraph.links = selectedGraph.links.filter(link =>
      // Both link.source and link.target should be associated with (contain the name of) genomes in selectedGenomes
      selectedGenomes.some(genome => link.source.includes(genome)) &&
      selectedGenomes.some(genome => link.target.includes(genome))
    );
  }

  // Select domain/graph to focus on
  function selectDomain(idx: number) {
    selectedGraph = graphs[idx];
    filterGraph();  // Reapply the filter to the selected graph
    console.log(selectedGraph)
  }

  async function handleUpload(coordinateFile: File | null, matrixFiles: File[], domainSpecific: boolean, closeFocus: boolean = false) {
    uploadedCoordsFile = coordinateFile;
    uploadedMatrixFiles = matrixFiles;
    isDomainSpecific = domainSpecific;
    loading = true; // Set loading to true to clear the graph
    try {
      await uploadFiles();
      if (closeFocus && chartComponent) {
        chartComponent.exitFocus();
      }
      showUploadModal = false;
    } catch (error) {
      loading = false; // Reset loading state on error
      throw error; // Pass the error back to the modal
    }
  }

  function handleDragStart(genome: string) {
    draggedGenome = genome;
  }

  function handleDragOver(e: DragEvent) {
    e.preventDefault();
  }

  function handleDrop(e: DragEvent, targetGenome: string) {
    e.preventDefault();
    if (!draggedGenome || draggedGenome === targetGenome) return;

    const fromIndex = selectedGenomes.indexOf(draggedGenome);
    const toIndex = selectedGenomes.indexOf(targetGenome);

    selectedGenomes = selectedGenomes.map((genome, index) => {
      if (index === fromIndex) return targetGenome;
      if (index === toIndex) return draggedGenome!;
      return genome;
    });

    draggedGenome = null;
  }
</script>

<!-- Main layout container -->
<div class="w-[95%] max-w-[1600px] mx-auto py-6">
  <div class="flex gap-6">
    <!-- Collapsible side panel -->
    <div class={`transition-all duration-300 ${isPanelCollapsed ? 'w-12' : 'w-80'} shrink-0`}>
      <div class="sticky top-[5.5rem]">
        <div class="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden flex flex-col max-h-[calc(100vh-7rem)]">
          <!-- Toggle button container -->
          <div class="p-2 bg-white border-b border-slate-200 flex justify-end shrink-0">
            <button
              on:click={() => isPanelCollapsed = !isPanelCollapsed}
              class="p-1.5 hover:bg-slate-100 rounded-md transition-colors cursor-pointer"
              aria-label={isPanelCollapsed ? "Expand panel" : "Collapse panel"}
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class={`transition-transform ${isPanelCollapsed ? 'rotate-180' : ''}`}>
                <polyline points="15 18 9 12 15 6"></polyline>
              </svg>
            </button>
          </div>

          <!-- Panel content - only show when not collapsed -->
          {#if !isPanelCollapsed}
            <div class="overflow-y-auto">
              <div class="p-4 space-y-4">
                <!-- Combined Genome Selection and Ordering -->
                <div class="space-y-2">
                  <h4 class="text-xs font-medium text-slate-800">Select and Arrange Genomes:</h4>
                  {#if selectedGraph.genomes}
                    <div class="space-y-2">
                      <!-- Selected Genomes Section -->
                      <div class="bg-green-50 rounded-lg p-2.5">
                        <h4 class="text-xs font-medium text-green-800 mb-1.5">Selected Genomes (drag to reorder)</h4>
                        {#if selectedGenomes.length === 0}
                          <p class="text-xs text-slate-500 italic">No genomes selected</p>
                        {:else}
                          <div class="space-y-1">
                            {#each selectedGenomes as genome}
                              <div
                                class="py-1.5 px-2 bg-white border border-green-200 rounded-md shadow-sm cursor-move flex items-center gap-2 hover:border-green-500 transition-colors text-sm"
                                draggable="true"
                                on:dragstart={() => handleDragStart(genome)}
                                on:dragover={handleDragOver}
                                on:drop={(e) => handleDrop(e, genome)}
                                role="button"
                                tabindex="0"
                              >
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-slate-400 shrink-0">
                                  <line x1="8" y1="6" x2="21" y2="6"></line>
                                  <line x1="8" y1="12" x2="21" y2="12"></line>
                                  <line x1="8" y1="18" x2="21" y2="18"></line>
                                  <line x1="3" y1="6" x2="3.01" y2="6"></line>
                                  <line x1="3" y1="12" x2="3.01" y2="12"></line>
                                  <line x1="3" y1="18" x2="3.01" y2="18"></line>
                                </svg>
                                <span class="flex-1 truncate">{genome}</span>
                                <button
                                  on:click={() => toggleGenomeSelection(genome)}
                                  class="p-0.5 hover:bg-red-100 rounded-full transition-colors cursor-pointer"
                                  title="Remove from selection"
                                  aria-label="Remove from selection"
                                >
                                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-red-500">
                                    <line x1="18" y1="6" x2="6" y2="18"></line>
                                    <line x1="6" y1="6" x2="18" y2="18"></line>
                                  </svg>
                                </button>
                              </div>
                            {/each}
                          </div>
                        {/if}
                      </div>

                      <!-- Available Genomes Section -->
                      <div class="bg-slate-100 rounded-lg p-2.5">
                        <h4 class="text-xs font-medium text-slate-800 mb-1.5">Available Genomes</h4>
                        <div class="space-y-1">
                          {#each selectedGraph.genomes.filter(g => !selectedGenomes.includes(g)) as genome}
                            <div
                              class="py-1.5 px-2 bg-white border border-slate-200 rounded-md shadow-sm flex items-center gap-2 hover:border-green-500 transition-colors text-sm"
                            >
                              <span class="flex-1 truncate">{genome}</span>
                              <button
                                on:click={() => toggleGenomeSelection(genome)}
                                class="p-0.5 hover:bg-green-100 rounded-full transition-colors cursor-pointer disabled:cursor-not-allowed"
                                title="Add to selection"
                                aria-label="Add to selection"
                                disabled={selectedGenomes.length >= 3}
                              >
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-green-500">
                                  <line x1="12" y1="5" x2="12" y2="19"></line>
                                  <line x1="5" y1="12" x2="19" y2="12"></line>
                                </svg>
                              </button>
                            </div>
                          {/each}
                        </div>
                      </div>

                      <button
                        on:click={filterGraph}
                        disabled={selectedGenomes.length !== 2 && selectedGenomes.length !== 3}
                        class="w-full px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 transition-colors duration-200 cursor-pointer disabled:bg-green-300 disabled:cursor-not-allowed"
                      >
                        Confirm Selection
                      </button>
                    </div>
                  {:else}
                    <p class="text-slate-600">Loading genomes...</p>
                  {/if}
                </div>

                <!-- Domain Selection -->
                {#if graphs.length > 1}
                  <div class="bg-slate-100 rounded-lg p-2.5">
                    <h4 class="text-xs font-medium text-slate-800 mb-1.5">View Domain:</h4>
                    <select
                      on:change={(e) => selectDomain((e.target as HTMLSelectElement).selectedIndex)}
                      class="w-full px-3 py-1.5 bg-white border border-slate-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-green-500 cursor-pointer"
                    >
                      {#each graphs as g, idx}
                        <option value={idx} selected={g === selectedGraph}>{g.domain_name}</option>
                      {/each}
                    </select>
                  </div>
                {/if}

                <!-- Cutoff Slider -->
                <div class="bg-slate-100 rounded-lg p-2.5">
                  <h4 class="text-xs font-medium text-slate-800 mb-1.5">Adjust Cut-off:</h4>
                  <div class="flex items-center gap-3">
                    <input
                      type="range"
                      min="55"
                      max="100"
                      disabled={selectedGraph.domain_name === "ALL"}
                      bind:value={cutoff}
                      class="flex-1 h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                    />
                    <span class="text-sm text-slate-600 tabular-nums w-8 text-right">{cutoff}%</span>
                  </div>
                </div>

                <!-- Link Filters -->
                <div class="bg-slate-100 rounded-lg p-2.5">
                  <h4 class="text-xs font-medium text-slate-800 mb-1.5">Link Filters:</h4>
                  {#if selectedGraph.domain_name === "ALL"}
                    <div class="space-y-1">
                      <label class="flex items-center gap-2 text-sm text-slate-700">
                        <input
                          type="checkbox"
                          bind:checked={showConsistent}
                          class="w-3.5 h-3.5 text-green-600 border-slate-300 rounded focus:ring-green-500 cursor-pointer"
                        />
                        Consistent Links
                      </label>
                      <label class="flex items-center gap-2 text-sm text-slate-700">
                        <input
                          type="checkbox"
                          bind:checked={showInconsistent}
                          class="w-3.5 h-3.5 text-green-600 border-slate-300 rounded focus:ring-green-500 cursor-pointer"
                        />
                        Inconsistent Links
                      </label>
                      <label class="flex items-center gap-2 text-sm text-slate-700">
                        <input
                          type="checkbox"
                          bind:checked={showPartiallyConsistent}
                          class="w-3.5 h-3.5 text-green-600 border-slate-300 rounded focus:ring-green-500 cursor-pointer"
                        />
                        Partially Consistent Links
                      </label>
                      <label class="flex items-center gap-2 text-sm text-slate-700">
                        <input
                          type="checkbox"
                          bind:checked={showNonReciprocal}
                          class="w-3.5 h-3.5 text-green-600 border-slate-300 rounded focus:ring-green-500 cursor-pointer"
                        />
                        Non-Reciprocal Links
                      </label>
                    </div>
                  {:else}
                    <div class="space-y-1">
                      <label class="flex items-center gap-2 text-sm text-slate-700">
                        <input
                          type="checkbox"
                          bind:checked={showReciprocal}
                          class="w-3.5 h-3.5 text-green-600 border-slate-300 rounded focus:ring-green-500 cursor-pointer"
                        />
                        Reciprocal Links
                      </label>
                      <label class="flex items-center gap-2 text-sm text-slate-700">
                        <input
                          type="checkbox"
                          bind:checked={showNonReciprocal}
                          class="w-3.5 h-3.5 text-green-600 border-slate-300 rounded focus:ring-green-500 cursor-pointer"
                        />
                        Non-Reciprocal Links
                      </label>
                    </div>
                  {/if}
                </div>
              </div>
            </div>
          {/if}
        </div>
      </div>
    </div>

    <!-- Main content area -->
    <div class="flex-1 min-w-0">
      {#if loading}
        <div class="flex justify-center items-center py-8">
          <div class="animate-spin rounded-full h-12 w-12 border-4 border-green-200"></div>
          <div class="animate-spin rounded-full h-12 w-12 border-4 border-green-600 border-t-transparent absolute"></div>
        </div>
      {:else}
        <!-- Top section with max-width to prevent expansion -->
        {#if (isAuthenticated && graphs.length > 0) || (groupId && (matrixFiles.length > 0 || coordinateFile))}
          <div class="mb-8">
            <!-- After upload or when viewing existing group -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <!-- Group info section for authenticated users -->
              <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
                <h3 class="text-xl font-semibold text-slate-800 mb-4">Group Information</h3>
                <div class="space-y-4">
                  <input
                    type="text"
                    placeholder="Title"
                    bind:value={title}
                    class="w-full px-4 py-2 bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  />
                  <textarea
                    placeholder="Description"
                    bind:value={description}
                    class="w-full px-4 py-2 bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                    rows="3"
                  ></textarea>

                  <button
                    on:click={saveGroup}
                    disabled={savingGroup}
                    class="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors duration-200 cursor-pointer disabled:bg-green-300 disabled:cursor-not-allowed"
                  >
                    {#if savingGroup}
                      <div class="flex items-center">
                        <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Saving...
                      </div>
                    {:else}
                      {groupId ? 'Update Group' : 'Save Group'}
                    {/if}
                  </button>
                </div>
              </div>

              {#if groupId && (matrixFiles.length > 0 || coordinateFile)}
                <!-- Download section only shown for existing groups -->
                <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
                  <h3 class="text-xl font-semibold text-slate-800 mb-3">Download Files</h3>
                  <div class="space-y-4">
                    {#if coordinateFile}
                      <div>
                        <h4 class="text-lg font-medium text-slate-700 mb-2">Coordinate File</h4>
                        <div class="flex flex-col gap-1.5">
                          <a href={coordinateFile.url} target="_blank" rel="noopener noreferrer" class="inline-block max-w-full">
                            <button class="inline-flex w-full items-center px-3 py-1.5 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors duration-200 cursor-pointer">
                              <span class="truncate flex-1 text-left">{coordinateFile.original_name}</span>
                              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="ml-2 shrink-0">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                                <polyline points="7 10 12 15 17 10"/>
                                <line x1="12" y1="15" x2="12" y2="3"/>
                              </svg>
                            </button>
                          </a>
                        </div>
                      </div>
                    {/if}
                    {#if matrixFiles.length > 0}
                      <div>
                        <h4 class="text-lg font-medium text-slate-700 mb-2">Matrix File{matrixFiles.length > 1 ? 's' : ''}</h4>
                        <div class="flex flex-col gap-1.5">
                          {#each matrixFiles as file}
                            <a href={file.url} target="_blank" rel="noopener noreferrer" class="inline-block max-w-full">
                              <button class="inline-flex w-full items-center px-3 py-1.5 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors duration-200 cursor-pointer">
                                <span class="truncate flex-1 text-left">{file.original_name}</span>
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="ml-2 shrink-0">
                                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                                  <polyline points="7 10 12 15 17 10"/>
                                  <line x1="12" y1="15" x2="12" y2="3"/>
                                </svg>
                              </button>
                            </a>
                          {/each}
                        </div>
                      </div>
                    {/if}
                  </div>
                </div>
              {/if}
            </div>
          </div>
        {/if}

        <!-- Graph visualization container -->
        <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-6 overflow-auto">
          {#if loading}
            <div class="flex justify-center items-center py-8">
              <div class="animate-spin rounded-full h-12 w-12 border-4 border-green-200"></div>
              <div class="animate-spin rounded-full h-12 w-12 border-4 border-green-600 border-t-transparent absolute"></div>
            </div>
          {:else if errorMessage}
            <div class="flex justify-center items-center py-8">
              <div class="max-w-lg">
                <p class="text-red-600 bg-red-50 p-4 rounded-lg text-center">{errorMessage}</p>
                <div class="flex justify-center mt-4">
                  <button
                    on:click={() => showUploadModal = true}
                    class="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors duration-200 cursor-pointer"
                  >
                    Try Again
                  </button>
                </div>
              </div>
            </div>
          {:else if !graphs.length}
            <div class="flex flex-col items-center justify-center py-8">
              <button
                on:click={() => showUploadModal = true}
                class="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors duration-200 cursor-pointer mb-3"
              >
                Upload and Prepare Graph
              </button>
              <p class="text-slate-600 text-center">Upload your files to visualize protein relationships</p>
            </div>
          {:else if !filteredGraph.nodes.length}
            <div class="flex justify-center items-center py-8">
              <p class="text-slate-600 text-center">Select genomes from the left panel to view the graph</p>
            </div>
          {:else}
            <Chart
              bind:this={chartComponent}
              graph={filteredGraph}
              {cutoff}
              {showReciprocal}
              {showNonReciprocal}
              {showConsistent}
              {showInconsistent}
              {showPartiallyConsistent}
            />
          {/if}
        </div>
      {/if}
    </div>
  </div>
</div>

<UploadModal
  isOpen={showUploadModal}
  onClose={() => showUploadModal = false}
  onUpload={handleUpload}
/>

<style>
  /* Empty style tag required for Tailwind processing */
</style>
