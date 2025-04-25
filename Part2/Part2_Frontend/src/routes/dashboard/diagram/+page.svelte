<script lang="ts">
  import Chart from '$lib/Chart.svelte';
  import dummyGraph from '$lib/dummy-graph.json';
  import testGraph from '$lib/test.json';
  import { onMount } from 'svelte';

  interface Node {
    id: string;
    genome_name: string;
    protein_name: string;
    direction: string;   // "plus" | "minus"
    rel_position: number;
    _dup?: boolean;      // internal flag for duplicated bottom‑row copy
  }

  interface Link {
    source: string;
    target: string;
    score: number;       // 0‑100
    is_reciprocal: boolean;
  }

  interface Graph {
    nodes: Node[];
    links: Link[];
    genomes: string[];   // list of genome names
  }

  let groupId: string | null = null;    // Group ID for file retrieval
  let graph: Graph = { nodes: [], links: [], genomes: [] };
  let selectedGenomes: string[] = [];
  let filteredGraph: Graph = { nodes: [], links: [], genomes: [] };
  let matrixFile: File | null = null;   // TODO: update to support multiple files
  let coordsFile: File | null = null;

  let errorMessage = "";
  let loading = false;        // Loading state for file upload
  let cutoff = 0;             // slider value
  let isDomainSpecific = false;

  // Form information if user choses to save graph
  let title = '';
  let description = '';
  let numGenes = 0;
  let numDomains = 1;

  onMount(async () => {
    const urlParams = new URLSearchParams(window.location.search);
    groupId = urlParams.get('groupId');

    if (groupId) {
      try {
        loading = true;
        const response = await fetch(`http://127.0.0.1:5000/get_group_graph?groupId=${groupId}`);

        if (!response.ok) {
          throw new Error(`Error fetching graph: ${response.statusText}`);
        }

        const fetchedGraph = await response.json();
        graph = fetchedGraph.graph;
        numGenes = fetchedGraph.num_genes;
        numDomains = fetchedGraph.num_domains;
        // Reset selected genomes and filtered graph
        selectedGenomes = [];
        filteredGraph = { nodes: [], links: [], genomes: [] };

        // Set the title and description if available
        title = fetchedGraph.title || '';
        description = fetchedGraph.description || '';
        loading = false;
      } catch (error) {
        errorMessage = error.message || "An error occurred.";
        console.error('Detailed error:', {
            status: error.response?.status,
            data: await error.response?.text()
        });
      }
    }
  });


  // Function to handle file uploads
  async function uploadFiles() {
    if (!coordsFile || !matrixFile) {
      alert('Please select matrix and coordinates files to upload.');
      return;
    }

    const formData = new FormData();
    formData.append('file_coordinate', coordsFile);
    formData.append('file_matrix', matrixFile);
    formData.append('is_domain_specific', isDomainSpecific ? 'true' : 'false');
    formData.append('username', localStorage.getItem('username') || ''); // Automatically send stored username

    try {
      // https://h47f781wh1.execute-api.us-east-1.amazonaws.com/dev/upload
      const response = await fetch('http://127.0.0.1:5000/generate_graph', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `Upload failed: ${response.statusText}`);
      }

      const fetchedGraph = await response.json();
      console.log('Fetched graph:', fetchedGraph);
      graph = fetchedGraph.graph;
      numGenes = fetchedGraph.num_genes;
      numDomains = fetchedGraph.num_domains;
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

    if (!coordsFile || !matrixFile) {
      alert('Please select matrix and coordinates files to upload.');
      return;
    }

    const formData = new FormData();
    formData.append('file_coordinate', coordsFile);
    formData.append('file_matrix', matrixFile);

    if (groupId) {
      formData.append('groupId', groupId); // Include groupId if available
    }
    formData.append('username', localStorage.getItem('username') || ''); // Automatically send stored username
    formData.append('title', title);
    formData.append('description', description);
    formData.append('num_genes', numGenes.toString());
    formData.append('num_domains', numDomains.toString());
    formData.append('is_domain_specific', isDomainSpecific ? 'true' : 'false');
    formData.append('genomes', JSON.stringify(graph.genomes));

    try {
      const response = await fetch('http://127.0.0.1:5000/save', {
        method: 'POST',
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
      alert('Group saved successfully!');
    } catch (error) {
      console.error('Error saving group:', error);
      alert('Failed to save group. Please try again.');
    }
  }

  // Function to switch data source
  function switchDataSource(source: string) {
    if (source === 'dummy') {
      graph = dummyGraph;
    } else if (source === 'test') {
      graph = testGraph;
    } else {
      console.error('Invalid data source:', source);
      return;
    }

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
    filteredGraph.nodes = graph.nodes.filter(node =>
      selectedGenomes.includes(node.genome_name)
    );

    // Update links in filtered graph
    filteredGraph.links = graph.links.filter(link =>
      // Both link.source and link.target should be associated with (contain the name of) genomes in selectedGenomes
      selectedGenomes.some(genome => link.source.includes(genome)) &&
      selectedGenomes.some(genome => link.target.includes(genome))
    );
  }
</script>

{#if loading}
  <p>Loading...</p>
{:else}

  <!-- File upload/data source section only available if not reviewing a specific group -->
  {#if !groupId}
    <!-- File upload section -->
    <div style="margin: 1rem; display: flex; justify-content: space-between; align-items: center; gap: 1rem;">
      <div>
        <h3>Upload Coordinates File:</h3>
        <input type="file" on:change={(e) => coordsFile = (e.target as HTMLInputElement).files?.[0] || null} />
      </div>
      <div>
        <h3>Upload Matrix File:</h3>
        <input type="file" on:change={(e) => matrixFile = (e.target as HTMLInputElement).files?.[0] || null} />
      </div>
      <label>
        <input type="checkbox" bind:checked={isDomainSpecific} disabled/>
        Domain-Specific?
      </label>
      <button on:click={uploadFiles} disabled={!matrixFile || !coordsFile}>Upload and Prepare Graph</button>
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
  {#if graph.nodes.length > 0}
    <div style="margin: 1rem; margin-top: 0px; display: flex; flex-direction: column; gap: 1rem; max-width: 300px;">
      <h3>Save Group</h3>
      <input type="text" placeholder="Title" bind:value={title} />
      <textarea placeholder="Description" bind:value={description}></textarea>
      <button on:click={saveGroup}>Save Group</button>
    </div>
  {/if}

  <!-- Genome selection checkboxes, filter button, and cutoff slider in one row -->
  <div style="margin: 1rem; display: flex; align-items: center; gap: 2rem;">
    <div>
      <h3>Select 3 Genomes:</h3>
      {#if graph.genomes}
        {#each graph.genomes as genome}
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
      <input type="range" min="0" max="100" bind:value={cutoff}/>
      {cutoff}%
    </label>
  </div>

  <Chart graph={filteredGraph} {cutoff}/>
{/if}

<!-- Removed general styles, only using inline styles for specific elements -->
<!-- TODO: incorporate tailwindcss for cleaner styling -->
