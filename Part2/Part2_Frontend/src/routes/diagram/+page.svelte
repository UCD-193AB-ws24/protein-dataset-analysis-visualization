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

  const nodes = [
    // Red nodes
    { color: 'red', row: 0, x: 0.1, direction: 'right', metadata: 'Red node 1' },
    { color: 'red', row: 1, x: 0.3, direction: 'right', metadata: 'Red node 2' },
    { color: 'red', row: 2, x: 0.1, direction: 'right', metadata: 'Red node 3' },
    { color: 'red', row: 3, x: 0.1, direction: 'right', metadata: 'Red node 4' },

    // Orange nodes
    { color: 'orange', row: 0, x: 0.3, direction: 'left', metadata: 'Orange node 1' },
    { color: 'orange', row: 1, x: 0.1, direction: 'left', metadata: 'Orange node 2' },
    { color: 'orange', row: 2, x: 0.3, direction: 'left', metadata: 'Orange node 3' },
    { color: 'orange', row: 3, x: 0.3, direction: 'left', metadata: 'Orange node 4' },
    // Blue nodes
    { color: 'blue', row: 0, x: 0.5, direction: 'left', metadata: 'Blue node 1' },
    { color: 'blue', row: 3, x: 0.5, direction: 'left', metadata: 'Blue node 2' },

    // Green nodes
    { color: 'green', row: 0, x: 0.7, direction: 'right', metadata: 'Green node 1' },
    { color: 'green', row: 2, x: 0.7, direction: 'right', metadata: 'Green node 2' },
    { color: 'green', row: 3, x: 0.9, direction: 'right', metadata: 'Green node 3' }
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

    // Draw connections between rows
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

    // Draw each node as a "centered arrow":
    // The node coordinate is at x=0 in the arrow path,
    // so we translate the arrow so that x=0,y=0 lines up with the node.

    // On hover, nodes will have a tooltip with additional information
    const tooltip = d3.select('#tooltip');

    svg.selectAll('path.node')
      .data(nodes)
      .enter()
      .append('path')
      .attr('class', 'node')
      .attr('fill', d => d.color)
      .attr('d', d => {
        if (d.direction === 'right') {
          /*
            An arrow 40px wide, 20px tall, with the boundary between
            the rectangular tail and triangular tip at x=0, so the
            "node coordinate" is in the middle.

            1) Rectangle from x=-40..0, y=-10..+10
            2) Triangle from (0,-20) -> (40,0) -> (0,20)
          */
          return `
            M -40,-10 L 0,-10 L 0,10 L -40,10 Z
            M 0,-20 L 40,0 L 0,20 Z
          `;
        } else {
          /*
            Same shape mirrored horizontally:
            1) Rectangle from x=0..40, y=-10..+10
            2) Triangle from (0,-20) -> (-40,0) -> (0,20)
          */
          return `
            M 40,-10 L 0,-10 L 0,10 L 40,10 Z
            M 0,-20 L -40,0 L 0,20 Z
          `;
        }
      })
      .attr('transform', d => {
        const px = xScale(d.x);
        const py = yScale(d.row) + yScale.bandwidth() / 2;
        return `translate(${px}, ${py})`;
      })
      // 1) Mouse over: show tooltip and set text
      .on('mouseover', function(event, d) {
        tooltip
          .style('opacity', 1)
          .style('color', d.color)
          // .html(`<strong>${d.color}</strong><br/>${d.metadata}`);
          .text(`${d.metadata}`);
        // Optionally highlight the hovered arrow
        d3.select(this).style('opacity', 0.8);
      })
      // 2) Mouse move: reposition tooltip near mouse
      .on('mousemove', function(event) {
        tooltip
          .style('left', (event.pageX + 10) + 'px')
          .style('top', (event.pageY + 10) + 'px');
      })
      // 3) Mouse out: hide tooltip
      .on('mouseout', function() {
        tooltip.style('opacity', 0);
        d3.select(this).style('opacity', 1);
      });


  });
</script>

<div id="chart"></div>
<!-- A hidden tooltip (initially) -->
<div
  id="tooltip"
  style="
    position: absolute;
    pointer-events: none;
    background: white;
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 6px;
    opacity: 0;
    transition: opacity 0.15s;
  "
></div>

<style>
  /*
  Using global since connections are generated dynamically;
  svelte can't immediately recognize them
  */
  :global(.connection) {
    transition: 0.15s;
  }
  :global(.connection:hover) {
    stroke-width: 6;
  }
</style>
