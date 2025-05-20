<script lang="ts">
  import Chart from '$lib/Chart.svelte';
  import dummyGraph from '$lib/dummy-graph.json';
  import testGraph from '$lib/test.json';
  import { onMount } from 'svelte';
  import { API_BASE_URL } from '$lib/api';
  import { goto } from '$app/navigation'; // Import SvelteKit's navigation function
  import { oidcClient } from '$lib/auth'
	import { getTokens } from '$lib/getTokens';

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

  let graphs: Graph[] = [];
  let selectedGraph: Graph = { nodes: [], links: [], genomes: [] }; // Current graph to be displayed
  let selectedGenomes: string[] = [];
  let filteredGraph: Graph = { nodes: [], links: [], genomes: [] };

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

  let idToken = '';
	let accessToken = '';

  onMount(async () => {
    const urlParams = new URLSearchParams(window.location.search);
    const initialId = urlParams.get('groupId');
    const tokens = await getTokens();
    idToken = tokens.idToken;
    accessToken = tokens.accessToken;


    if (initialId) {
      groupId = initialId;
      await fetchGroupData(groupId);
    }

    loading = false; // Set loading to false after fetching data
  });

  function normaliseGraphs(data: any): Graph[] {
    // backend might return {graphs:[…]} (new) or {graph:{…}} (legacy)
    if (Array.isArray(data?.graphs)) return data.graphs;
    if (data?.graph) return [data.graph];
    // direct object passed (e.g. dummyGraph)
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
      errorMessage = error.message || "An error occurred.";
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
    formData.append('file_coordinate', uploadedCoordsFile); // Use the uploaded coordinate file
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
      errorMessage = error.message || "An error occurred.";
      console.error('Detailed error:', {
          status: error.response?.status,
          data: await error.response?.text()
      });
    }
  }

  // Function to save the group of files
  async function saveGroup() {
    if (!title) {
      alert('Please provide a title for the group of files.');
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
      formData.append('group_id', groupId); // Include groupId if available
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
          Authorization: `Bearer ${accessToken}`,
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

  // Function to switch data source
  function switchDataSource(source: string) {
    graphs = [source === 'dummy' ? dummyGraph : testGraph];
    selectedGraph  = graphs[0];
    isDomainSpecific = false;
    numGenes = selectedGraph.nodes.length;
    numDomains = 1;

    selectedGenomes = []; // Reset selected genomes when switching data source
    filteredGraph = { nodes: [], links: [], genomes: [] }; // Reset filtered graph
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
    if (selectedGenomes.length !== 3) {
      console.error('Please select exactly 3 genomes to filter the graph.');
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
</script>

{#if loading}
  <p>Loading...</p>
{:else}
  <!-- File download section -->
  {#if groupId && (matrixFiles.length > 0 || coordinateFile)}
    <div style="margin: 1rem;">
      <h3>Download Files</h3>
      {#if coordinateFile}
        <div>
          <a href={coordinateFile.url} target="_blank" rel="noopener noreferrer">
            <button>Download Coordinate File ({coordinateFile.original_name})</button>
          </a>
        </div>
      {/if}
      {#each matrixFiles as file, index}
        <div>
          <a href={file.url} target="_blank" rel="noopener noreferrer">
            <button>Download Matrix File {index + 1} ({file.original_name})</button>
          </a>
        </div>
      {/each}
    </div>
  {/if}

  <!-- File upload/data source section only available if not reviewing a specific group -->
  {#if !groupId}
    <!-- File upload section -->
    <div style="margin: 1rem; display: flex; justify-content: space-between; align-items: center; gap: 1rem;">
      <div>
        <h3>Upload Coordinate File:</h3>
        <input type="file" on:change={(e) => uploadedCoordsFile = (e.target as HTMLInputElement).files?.[0] || null} />
      </div>
      <div>
        <h3>Upload Matrix Files:</h3>
        <input type="file" multiple={isDomainSpecific} on:change={(e) => uploadedMatrixFiles = Array.from((e.target as HTMLInputElement).files || [])} />
        <p style="font-size: 0.8rem; color: gray;">{isDomainSpecific ? 'Select up to 3 matrix files.' : 'Select only 1 matrix file.'}</p>
      </div>
      <label>
        <input type="checkbox" bind:checked={isDomainSpecific} />
        Domain-Specific?
      </label>
      <button on:click={uploadFiles} disabled={!uploadedCoordsFile || uploadedMatrixFiles.length === 0 || (isDomainSpecific && uploadedMatrixFiles.length > 3)}>Upload and Prepare Graph</button>
      {#if errorMessage}
            <p class="error">{errorMessage}</p>
      {/if}
    </div>

    <!-- Buttons to switch data source -->
    <div style="margin: 1rem; display: flex; align-items: center; gap: 1rem;">
      <h3>Or, use dummy data:</h3>
      <button on:click={() => switchDataSource('dummy')}>Dummy Data</button>
      <button on:click={() => switchDataSource('test')}>Test Data</button>
    </div>

    <hr>
  {/if}

  <!-- Save group section -->
  {#if selectedGraph.nodes.length > 0 && accessToken && idToken}
    <div style="margin: 1rem; margin-top: 0px; display: flex; flex-direction: column; gap: 1rem; max-width: 300px;">
      <h3>Save Group</h3>
      <input type="text" placeholder="Title" bind:value={title} />
      <textarea placeholder="Description" bind:value={description}></textarea>
      <button on:click={saveGroup}>Save Group</button>
    </div>
  {/if}

  <!-- Domain Selector -->
  {#if graphs.length > 1}
    <div style="margin: 1rem; display:flex; align-items:center; gap:0.5rem;">
      <span style="font-weight:600;">View domain:</span>
      <select on:change={(e) => selectDomain((e.target as HTMLSelectElement).selectedIndex)}>
        {#each graphs as g, idx}
          <option value={idx} selected={g === selectedGraph}>{g.domain_name}</option>
        {/each}
      </select>
    </div>
  {/if}

  <!-- Genome selection checkboxes, filter button, and cutoff slider in one row -->
  <div style="margin: 1rem; display: flex; align-items: center; gap: 2rem;">
    <div>
      <h3>Select 3 Genomes:</h3>
      {#if selectedGraph.genomes}
        {#each selectedGraph.genomes as genome}
          <label style="display: block; margin-top: 1rem; margin-left: 5%;">
            <input
              type="checkbox"
              value={genome}
              on:change={() => toggleGenomeSelection(genome)}
              checked={selectedGenomes.includes(genome)}
            />
            {genome}
          </label>
        {/each}
      {:else}
        <p>Loading genomes...</p>
      {/if}
    </div>

    <button on:click={filterGraph} disabled={selectedGenomes.length !== 3}>
      Confirm Selection
    </button>

    <label style="display: flex; align-items: center; gap: 0.5rem;">
      Adjust Cut-off:
      <input
        type="range"
        min="55"
        max="100"
        disabled={selectedGraph.domain_name === "ALL"}
        bind:value={cutoff}/>
      {cutoff}%
    </label>
  </div>

  <Chart graph={filteredGraph} {cutoff}/>
{/if}

<!-- Removed general styles, only using inline styles for specific elements -->
<!-- TODO: incorporate tailwindcss for cleaner styling -->
