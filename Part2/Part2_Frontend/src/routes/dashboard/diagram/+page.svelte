<script lang="ts">
  import Chart from '$lib/Chart.svelte';
  import dummyGraph from '$lib/dummy-graph.json';
  import testGraph from '$lib/test.json';

  let graph = dummyGraph;
  let cutoff = 0;            // slider value

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
  }
</script>

<Chart {graph} {cutoff}/>

<!-- Buttons to switch data source -->
<div style="margin: 1rem; display: flex; gap: 1rem;">
  <button on:click={() => switchDataSource('dummy')}>Dummy Data</button>
  <button on:click={() => switchDataSource('test')}>Test Data</button>
</div>

<label>
  Adjust Cut-off:
  <input type="range" min="0" max="100" bind:value={cutoff}/>
  {cutoff}%
</label>

<style>
  label {
    display: block;
    margin-top: 1rem;
    margin-left: 5%;
  }
</style>
