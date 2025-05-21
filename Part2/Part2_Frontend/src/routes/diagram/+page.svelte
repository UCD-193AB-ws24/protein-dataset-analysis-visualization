<script lang="ts">
  import Chart from '$lib/Chart.svelte';
  import { onMount } from 'svelte';
  import { API_BASE_URL } from '$lib/api';
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
  let cutoff = 55;           // slider value

  // Form information if user choses to save graph
  let title = '';
  let description = '';
  let numGenes = 0;
  let numDomains = 1;

  let showUploadModal = false;

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
    if (!uploadedCoordsFile || uploadedMatrixFiles.length === 0) {
      alert('Please select the required files.');
      return;
    }
    if (!isDomainSpecific && uploadedMatrixFiles.length !== 1) {
      alert('Exactly one matrix file is required for non-domain-specific graphs.');
      return;
    }
    if (isDomainSpecific && uploadedMatrixFiles.length > 3) {
      alert('Up to three matrix files are supported for domain-specific graphs.');
      return;
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
      errorMessage = error instanceof Error ? error.message : "An error occurred.";
      console.error('Detailed error:', error);
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

    const formData = new FormData();
    if (!groupId) {
      // For new groups, validate uploaded files
      if (!uploadedCoordsFile || uploadedMatrixFiles.length === 0) {
        alert('Please select at least one coordinate file and one matrix file to save.');
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

  function handleUpload(coordinateFile: File | null, matrixFiles: File[], domainSpecific: boolean) {
    uploadedCoordsFile = coordinateFile;
    uploadedMatrixFiles = matrixFiles;
    isDomainSpecific = domainSpecific;
    uploadFiles();
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

{#if loading}
  <div class="flex justify-center items-center py-8">
    <div class="animate-spin rounded-full h-12 w-12 border-4 border-green-200"></div>
    <div class="animate-spin rounded-full h-12 w-12 border-4 border-green-600 border-t-transparent absolute"></div>
  </div>
{:else}
  <div class="container mx-auto px-4 py-8">
    <!-- File download and Save group sections side by side -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
      <!-- File download section -->
      {#if groupId && (matrixFiles.length > 0 || coordinateFile)}
        <div class="p-6 bg-white rounded-lg shadow-sm border border-slate-200">
          <h3 class="text-xl font-semibold text-slate-800 mb-4">Download Files</h3>
          <div class="flex flex-col gap-3">
            {#if coordinateFile}
              <a href={coordinateFile.url} target="_blank" rel="noopener noreferrer" class="inline-block">
                <button class="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors duration-200 cursor-pointer">
                  Download Coordinate File ({coordinateFile.original_name})
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="ml-2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                    <polyline points="7 10 12 15 17 10"/>
                    <line x1="12" y1="15" x2="12" y2="3"/>
                  </svg>
                </button>
              </a>
            {/if}
            {#each matrixFiles as file, index}
              <a href={file.url} target="_blank" rel="noopener noreferrer" class="inline-block">
                <button class="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors duration-200 cursor-pointer">
                  Download Matrix File {index + 1} ({file.original_name})
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="ml-2">
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

      <!-- Save group section -->
      {#if selectedGraph.nodes.length > 0 && isAuthenticated}
        <div class="p-6 bg-white rounded-lg shadow-sm border border-slate-200">
          <h3 class="text-xl font-semibold text-slate-800 mb-4">Save Group</h3>
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
              class="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors duration-200 cursor-pointer"
            >
              Save Group
            </button>
          </div>
        </div>
      {/if}
    </div>

    <!-- File upload/data source section only available if not reviewing a specific group -->
    {#if !groupId}
      <!-- File upload section -->
      <div class="mb-8 p-6 bg-white rounded-lg shadow-sm border border-slate-200">
        <div class="inline-block">
          <button
            on:click={() => showUploadModal = true}
            class="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors duration-200 cursor-pointer disabled:bg-green-300 disabled:cursor-not-allowed"
          >
            Upload and Prepare Graph
          </button>
        </div>
      </div>
    {/if}

    {#if errorMessage}
      <div class="mb-8">
        <p class="text-red-600 bg-red-50 p-4 rounded-lg">{errorMessage}</p>
      </div>
    {/if}

    <!-- Genome selection and controls -->
    <div class="mb-8 p-6 bg-white rounded-lg shadow-sm border border-slate-200">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
        <div>
          <h3 class="text-lg font-semibold text-slate-800 mb-4">Select Genomes:</h3>
          {#if selectedGraph.genomes}
            <div class="space-y-2">
              {#each selectedGraph.genomes as genome}
                <label class="flex items-center gap-2 text-slate-700">
                  <input
                    type="checkbox"
                    value={genome}
                    on:change={() => toggleGenomeSelection(genome)}
                    checked={selectedGenomes.includes(genome)}
                    class="w-4 h-4 text-green-600 border-slate-300 rounded focus:ring-green-500"
                  />
                  {genome}
                </label>
              {/each}
            </div>
          {:else}
            <p class="text-slate-600">Loading genomes...</p>
          {/if}
        </div>

        <div class="flex flex-col gap-4">
          <div class="flex justify-center">
            <button
              on:click={filterGraph}
              disabled={selectedGenomes.length !== 2 && selectedGenomes.length !== 3}
              class="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors duration-200 cursor-pointer disabled:bg-green-300 disabled:cursor-not-allowed"
            >
              Confirm Selection
            </button>
          </div>

          {#if graphs.length > 1}
            <div class="flex items-center gap-4">
              <span class="text-lg font-semibold text-slate-800">View domain:</span>
              <select
                on:change={(e) => selectDomain((e.target as HTMLSelectElement).selectedIndex)}
                class="px-4 py-2 bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
              >
                {#each graphs as g, idx}
                  <option value={idx} selected={g === selectedGraph}>{g.domain_name}</option>
                {/each}
              </select>
            </div>
          {/if}
        </div>

        <div>
          <label class="flex items-center gap-4 text-slate-700">
            <span class="text-lg font-semibold">Adjust Cut-off:</span>
            <input
              type="range"
              min="55"
              max="100"
              disabled={selectedGraph.domain_name === "ALL"}
              bind:value={cutoff}
              class="w-full"
            />
            <span class="min-w-[3rem] text-center">{cutoff}%</span>
          </label>
        </div>
      </div>

      {#if selectedGenomes.length === 3 || selectedGenomes.length === 2}
        <div class="mt-8 p-4 bg-slate-50 rounded-lg">
          <h4 class="text-lg font-semibold text-slate-800 mb-4">Arrange Genome Order:</h4>
          <div class="flex flex-col gap-2">
            {#each selectedGenomes as genome}
              <div
                class="p-3 bg-white border border-slate-200 rounded-lg shadow-sm cursor-move flex items-center gap-2"
                draggable="true"
                on:dragstart={() => handleDragStart(genome)}
                on:dragover={handleDragOver}
                on:drop={(e) => handleDrop(e, genome)}
                role="button"
                tabindex="0"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-slate-400">
                  <line x1="8" y1="6" x2="21" y2="6"></line>
                  <line x1="8" y1="12" x2="21" y2="12"></line>
                  <line x1="8" y1="18" x2="21" y2="18"></line>
                  <line x1="3" y1="6" x2="3.01" y2="6"></line>
                  <line x1="3" y1="12" x2="3.01" y2="12"></line>
                  <line x1="3" y1="18" x2="3.01" y2="18"></line>
                </svg>
                {genome}
              </div>
            {/each}
          </div>
          <p class="mt-2 text-sm text-slate-600">Drag to reorder the genomes. The order will affect how they appear in the visualization.</p>
        </div>
      {/if}
    </div>

    <Chart graph={filteredGraph} {cutoff}/>

    <UploadModal 
      isOpen={showUploadModal}
      onClose={() => showUploadModal = false}
      onUpload={handleUpload}
    />
  </div>
{/if}

<style>
  /* Empty style tag required for Tailwind processing */
</style>
