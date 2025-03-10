<script>
  import { onMount } from 'svelte';
  import * as d3 from 'd3';
  import data from './data.json';
	import Chart from './Chart.svelte';

  //const nodes = data.nodes;
  //const connections = data.connections;
  let genomeNames = [];
  let nodeLists = [];
  let colors = [];
  let rowCount = 4;
  let geneCount = 5;
  let dataLoaded = false;

  async function fetchData() {
    // Here, data would be fetched from the server based on input files
    // for now, just "fetching" from the json file
    genomeNames = data.genomeNames;
    nodeLists = data.properNodeLists;
    colors = data.colors;
    dataLoaded = true;
  }
</script>


{#if dataLoaded}
  <Chart {genomeNames} {nodeLists} {colors} {rowCount} {geneCount} />
{:else}
  <div id="fetch">
    <button on:click={fetchData}>Fetch Data</button>
    <p>Click the button to fetch data</p>
  </div>
{/if}

<style>
  #fetch {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-top: 50px;
  }
</style>