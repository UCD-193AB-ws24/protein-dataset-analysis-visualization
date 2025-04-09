<script lang="ts">
  import Chart from '$lib/Chart.svelte';
  import graph from '$lib/dummy-graph.json';

  let cutoff = 0;            // slider value
</script>

<Chart {graph} {cutoff}/>

<label>
  Adjust Cut‑off:
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
