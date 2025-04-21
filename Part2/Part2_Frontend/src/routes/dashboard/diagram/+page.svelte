<script lang="ts">
  import Chart from '$lib/Chart.svelte';
  import dummyGraph from '$lib/dummy-graph.json';
  import testGraph from '$lib/test.json';

  let graph = dummyGraph;
  let cutoff = 0;            // slider value
  let selectedGenomes: string[] = [];
  let filteredGraph: typeof graph = { nodes: [], links: [], genomes: [] };
  let matrixFile: File | null = null;
  let coordsFile: File | null = null;

  // Function to handle file uploads
  async function uploadFiles() {
    if (!matrixFile || !coordsFile) {
      alert('Please select both matrix and coordinates files to upload.');
      return;
    }

    const formData = new FormData();
    formData.append('file_matrix', matrixFile);
    formData.append('file_coordinate', coordsFile);
    formData.append('username', localStorage.getItem('username') || ''); // Automatically send stored username

    try {
       // https://h47f781wh1.execute-api.us-east-1.amazonaws.com/dev/upload
      const response = await fetch('http://127.0.0.1:5000/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch graph data: ${response.statusText}`);
      }

      const fetchedGraph = await response.json();
      graph = fetchedGraph.graph; // Update the graph with the fetched data
      selectedGenomes = []; // Reset selected genomes
      filteredGraph = { nodes: [], links: [], genomes: [] }; // Reset filtered graph
    } catch (error) {
      console.error('Error uploading files:', error);
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

<!-- File upload section -->
<div style="margin: 1rem; display: flex; align-items: center; gap: 1rem;">
  <div>
    <h3>Upload Matrix File:</h3>
    <input type="file" on:change={(e) => matrixFile = (e.target as HTMLInputElement).files?.[0] || null} />
  </div>
  <div>
    <h3>Upload Coordinates File:</h3>
    <input type="file" on:change={(e) => coordsFile = (e.target as HTMLInputElement).files?.[0] || null} />
  </div>
  <button on:click={uploadFiles} disabled={!matrixFile || !coordsFile}>Upload and Prepare Graph</button>
</div>

<!-- Buttons to switch data source -->
<div style="margin: 1rem; display: flex; align-items: center; gap: 1rem;">
  <h3>Or, use dummy data:</h3>
  <button on:click={() => switchDataSource('dummy')}>Dummy Data</button>
  <button on:click={() => switchDataSource('test')}>Test Data</button>
</div>

<!-- Genome selection checkboxes, filter button, and cutoff slider in one row -->
<div style="margin: 1rem; display: flex; align-items: center; gap: 2rem;">
  <div>
    <h3>Select 3 Genomes:</h3>
    {#if graph.genomes}
      {#each graph.genomes as genome}
        <label style="display: block;">
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

<style>
  label {
    display: block;
    margin-top: 1rem;
    margin-left: 5%;
  }
</style>
