<script>
  import { onMount } from 'svelte';
  import * as d3 from 'd3';

  // we have 4 rows (0..3) and some hardcoded connections between them
  const rowCount = 4;
  const connections = [
    // each connection has color & from/to positions
    { color: 'red',   from: { row: 0, x: 0.1 }, to: { row: 1, x: 0.3 } },
    { color: 'red',   from: { row: 1, x: 0.3 }, to: { row: 2, x: 0.1 } },
    { color: 'red',   from: { row: 2, x: 0.1 }, to: { row: 3, x: 0.1 } },
    { color: 'orange',from: { row: 0, x: 0.3 }, to: { row: 1, x: 0.1 } },
    { color: 'orange',from: { row: 1, x: 0.1 }, to: { row: 2, x: 0.3 } },
    { color: 'orange',from: { row: 2, x: 0.3 }, to: { row: 3, x: 0.3 } },
    { color: 'blue',  from: { row: 0, x: 0.5 }, to: { row: 3, x: 0.5 } },
    { color: 'green', from: { row: 0, x: 0.7 }, to: { row: 2, x: 0.7 } },
    { color: 'green', from: { row: 2, x: 0.7 }, to: { row: 3, x: 0.9 } },

  ];

  let width = 600;
  let height = 200;

  onMount(() => {
    const svg = d3
      .select('#chart')
      .append('svg')
      .attr('width', width)
      .attr('height', height);

    // Define scales for x and y
    // We treat each row index as a discrete “band” on the y-axis
    const yScale = d3.scaleBand()
      .domain(d3.range(rowCount))   // [0, 1, 2, ... rowCount-1]
      .range([0, height])
      .paddingInner(0.2);

    // Can adjust x domain as needed (currently [0, 1]); we'll need to normalize
    // chromosome coordinates to this domain
    const xScale = d3.scaleLinear()
      .domain([0, 1])
      .range([0, width]);

    // Draw row lines
    svg.selectAll('line.row')
      .data(d3.range(rowCount))
      .enter()
      .append('line')
      .attr('class', 'row')
      .attr('x1', 0)
      .attr('x2', width)
      // center each line in the band
      .attr('y1', d => yScale(d) + yScale.bandwidth()/2)
      .attr('y2', d => yScale(d) + yScale.bandwidth()/2)
      .attr('stroke', 'black')
      .attr('stroke-width', 2);

    // 4. Define an arrow marker in <defs> to use on paths
    // svg.append('defs')
    //   .append('marker')
    //     .attr('id', 'arrow')
    //     .attr('viewBox', '0 0 10 10')
    //     .attr('refX', 5) // halfway so arrow tip sits at path's end
    //     .attr('refY', 5)
    //     .attr('markerWidth', 6)
    //     .attr('markerHeight', 6)
    //     .attr('orient', 'auto') // auto-orients the arrow with path
    //   .append('path')
    //     .attr('d', 'M0,0 L10,5 L0,10 Z')
    //     .attr('fill', 'currentColor'); // so it matches stroke color

    // 5. Draw connections between rows
    const lineGenerator = d3.line();

    svg.selectAll('path.connection')
      .data(connections)
      .enter()
      .append('path')
      .attr('class', 'connection')
      .attr('fill', 'none')
      .attr('stroke', d => d.color)
      .attr('stroke-width', 2)
      // Use line generator with two points [start, end].
      .attr('d', d => {
        const points = [
          [ xScale(d.from.x), yScale(d.from.row) + yScale.bandwidth()/2 ],
          [ xScale(d.to.x),   yScale(d.to.row)   + yScale.bandwidth()/2 ],
        ];
        return lineGenerator(points);
      })
      // attach arrow marker at the end of the path
      .attr('marker-end', 'url(#arrow)');
  });
</script>

<div id="chart"></div>

<!-- <style>
  /* Optional styling */
  .connection {
    transition: 0.15s;
  }
  .connection:hover {
    stroke-width: 4;
  }
</style> -->
