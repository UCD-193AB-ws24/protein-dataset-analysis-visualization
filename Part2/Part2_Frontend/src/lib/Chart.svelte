<script lang="ts">
  import { onMount, afterUpdate } from 'svelte';
  import * as d3 from 'd3';
  import UnionFind from '$lib/UnionFind';

  /**
   * Props
   *  - graph  : { genomes, nodes, links }
   *  - cutoff : similarity threshold (0‑100). Links with score < cutoff are hidden.
   */
  export let graph: {
    genomes: string[];
    nodes: Node[];
    links: Link[];
  };
  export let cutoff: number = 55;

  interface Node {
    id: string;
    genome_name: string;
    protein_name: string;
    direction: string;   // "plus" | "minus"
    rel_position: number;
    is_present?: boolean;
    gene_type?: string;
    _dup?: boolean;      // internal flag for duplicated bottom‑row copy
  }

  type ScoreLink = {
    source: string;
    target: string;
    score: number;
    is_reciprocal: boolean;
  };

  type CompareLink = {
    source: string;
    target: string;
    link_type: string; // "solid_color" | "dotted_grey" | etc.
  };

  type Link = ScoreLink | CompareLink;

  // ────────────────────────────────────────────────────────────────
  //  DOM refs / constants
  // ────────────────────────────────────────────────────────────────
  let labelSvgEl: SVGSVGElement;
  let chartSvgEl: SVGSVGElement;
  let tooltipEl: HTMLDivElement;

  const labelWidth = 120;
  const viewportWidth = 1000;
  const height = 600;
  const margin = { top: 20, right: 40, bottom: 20, left: 20 };
  const arrowHalf = 40;

  const strokeW = d3.scaleLinear<number, number>().domain([0, 100]).range([0.5, 3]);

  function arrowPath(dir: string): string {
    return dir === 'plus'
      ? 'M -30,-15 L 10,-15 L 10,15 L -30,15 Z M 10,-15 L 30,0 L 10,15 Z'
      : 'M 30,-15 L -10,-15 L -10,15 L 30,15 Z M -10,-15 L -30,0 L -10,15 Z';
  }

  /* duplicate first‑genome nodes to bottom row */
  function massage(original: typeof graph) {
    if (!original) return {
      nodes: [] as Node[],
      links: [] as Link[],
      genomes: [] as string[]
    };
    const genomes = original.genomes;
    const firstGenome = genomes[0];
    const dupSuffix = '__dup';

    const nodes: Node[] = [...original.nodes];
    const dupMap = new Map<string, string>();
    
    // Only duplicate if there are more than 2 genomes
    if (genomes.length > 2) {
      original.nodes.forEach((n) => {
        if (n.genome_name === firstGenome) {
          const dupId = n.id + dupSuffix;
          dupMap.set(n.id, dupId);
          nodes.push({ ...n, id: dupId, _dup: true });
        }
      });
    }

    const genomeOf = new Map(nodes.map((n) => [n.id, n.genome_name]));
    const links: Link[] = original.links.map((l) => {
      const gSrc = genomeOf.get(l.source);
      const gTgt = genomeOf.get(l.target);
      if (!gSrc || !gTgt) return l;
      const rowSrc = genomes.indexOf(gSrc);
      const rowTgt = genomes.indexOf(gTgt);
      if (Math.abs(rowSrc - rowTgt) > 1) {
        return gSrc === firstGenome
          ? { ...l, source: dupMap.get(l.source)! }
          : { ...l, target: dupMap.get(l.target)! };
      }
      return l;
    })
    // Exclude links between genes of the same genome
    .filter((l) => genomeOf.get(l.source) !== genomeOf.get(l.target));

    // UnionFind to group connected components by color
    const uf = new UnionFind(nodes.map((n) => n.id));
    links.forEach((l) => {
      if ('is_reciprocal' in l && l.is_reciprocal) uf.union(l.source, l.target);
      if ('link_type' in l && (l.link_type === 'solid_color' || l.link_type === 'dotted_color')) uf.union(l.source, l.target);
    });

    // Add to union-find structure "links" between first-genome and duplicated nodes
    if (genomes.length > 2) {
      nodes.forEach((n) => {
        if (n._dup) {
          const originalId = n.id.slice(0, -dupSuffix.length);
          const originalNode = nodes.find((o) => o.id === originalId);
          if (originalNode) {
            uf.union(n.id, originalId);
          }
        }
      });
    }

    // Map CCs to colors
    const componentRoots = new Set(nodes.map((n) => uf.find(n.id)));
    const componentSize = new Map([...componentRoots].map((root) => [root, 0]));
    nodes.forEach((n) => {
      const root = uf.find(n.id);
      componentSize.set(root, (componentSize.get(root) || 0) + 1);
    });

    // Select nodes we want to color (non-singletons or CCs of size 2 with a dup)
    const colorRoots = [...componentRoots].filter(root => {
      const size = componentSize.get(root)!;
      // if it's a size-2 CC *and* one member is a dup, skip it
      if (size === 2 && nodes.some(n => uf.find(n.id) === root && n._dup)) {
        return false;
      }
      // otherwise color only if size > 1
      return size > 1;
    });

    const customColors = [
      "#1f77b4",
      "#ff7f0e",
      "#2ca02c",
      "#00bfff",
      "#9467bd",
      "#8c564b",
      "#e377c2",
      "#bcbd22",
      "#17becf",
      "#6b8e23",
      "#4682b4",
      "#dda0dd",
      "#40e0d0",
      "#ff69b4",
    ];
    const colorScale = d3.scaleOrdinal(customColors).domain(colorRoots);
    // const colorScale = d3.scaleOrdinal([...d3.schemeSet3]).domain(colorRoots);
    // Gray-out CCs not associated with colorRoots
    const nodeColor = new Map(
      nodes.map((n) => {
        if (n.is_present === false) return [n.id, '#e6e6e6']

        const root = uf.find(n.id);
        return [n.id, colorRoots.includes(root) ? colorScale(root) : '#7f7f7f'];
      })
    );

    return { nodes, links, genomes, nodeColor };
  }

  // ────────────────────────────────────────────────────────────────
  //  Render
  // ────────────────────────────────────────────────────────────────
  function draw() {
    const { nodes, links, genomes, nodeColor } = massage(graph);
    if (!nodes.length) return;

    // apply cutoff filter
    const visibleLinks = links.filter((l) => 'score' in l ? l.score >= cutoff : true);

    // scales
    const numRows = genomes.length > 2 ? genomes.length + 1 : genomes.length; // Updated so no extra line when there are only 2 genomes
    const y = d3.scaleBand<number>().domain(d3.range(numRows)).range([0, height - margin.top - margin.bottom]).padding(0.6);
    const xExtent = d3.extent(nodes, (d) => d.rel_position) as [number, number];
    const spacing = 100;
    const chartWidth = Math.max(viewportWidth, (xExtent[1] - xExtent[0]) * spacing + arrowHalf * 2 + margin.left + margin.right);
    const x = d3.scaleLinear<number, number>().domain(xExtent).range([arrowHalf + margin.left, chartWidth - arrowHalf - margin.right]);

    const nodeById = new Map(nodes.map((n) => [n.id, n]));
    const rowOf = (n: Node) => (n._dup ? genomes.length : genomes.indexOf(n.genome_name));

    // ── LABELS ──
    const labelSvg = d3.select(labelSvgEl).attr('width', labelWidth).attr('height', height);
    labelSvg.selectAll('*').remove();
    const yLabels = genomes.length > 2 ? [...genomes, genomes[0]] : genomes; // Updated so that the first genome is duplicated only when there are more than 2 genomes
    labelSvg
      .append('g')
      .attr('transform', `translate(${labelWidth - 10},${margin.top})`)
      .selectAll('text')
      .data(yLabels)
      .enter()
      .append('text')
      .attr('y', (_, i) => y(i)! + y.bandwidth() / 2)
      .attr('dy', '0.35em')
      .attr('text-anchor', 'end')
      .style('font-size', '12px')
      .text((d) => d);

    // ── CHART ──
    const chartSvg = d3.select(chartSvgEl).attr('width', chartWidth).attr('height', height);
    chartSvg.selectAll('*').remove();

    const defs = chartSvg.append('defs');
    defs
      .append('clipPath')
      .attr('id', 'clip')
      .append('rect')
      .attr('x', margin.left)
      .attr('y', margin.top)
      .attr('width', chartWidth - margin.left - margin.right)
      .attr('height', height - margin.top - margin.bottom);

    const content = chartSvg
      .append('g')
      .attr('clip-path', 'url(#clip)')
      .append('g');

    // ── HORIZONTAL LINES ──
    content
      .append('g')
      .selectAll('line')
      .data(d3.range(numRows))
      .enter()
      .append('line')
      .attr('x1', margin.left)
      .attr('x2', chartWidth - margin.right)
      .attr('y1', (d) => y(d)! + y.bandwidth() / 2 + margin.top)
      .attr('y2', (d) => y(d)! + y.bandwidth() / 2 + margin.top)
      .attr('stroke', '#000')
      .attr('stroke-width', 2)

    // LINKS
    const linkSel = content
      .append('g')
      .selectAll('line')
      .data(visibleLinks)
      .enter()
      .append('line')
      .attr('x1', (d) => x(nodeById.get(d.source)!.rel_position))
      .attr('y1', (d) => y(rowOf(nodeById.get(d.source)!))! + y.bandwidth() / 2 + margin.top)
      .attr('x2', (d) => x(nodeById.get(d.target)!.rel_position))
      .attr('y2', (d) => y(rowOf(nodeById.get(d.target)!))! + y.bandwidth() / 2 + margin.top)
      .attr('stroke-width', (d) => strokeW('score' in d ? d.score : 100) * 2)
      .attr('stroke-dasharray', d => {
        if ('is_reciprocal' in d) return d.is_reciprocal ? null : '4,4';
        if ('link_type' in d) return d.link_type.includes('dotted') ? '4,4' : null;
        return null;
      })
      .attr('stroke', d => {
        if ('is_reciprocal' in d) return d.is_reciprocal ? nodeColor.get(d.source)! : '#bbb';
        if ('link_type' in d) {
          if (d.link_type === 'solid_red') return 'red';
          return d.link_type.includes('color') ? nodeColor.get(d.source)! : '#bbb';
        }
        return '#bbb';
      })
      .on('mouseover', function (event, d) {
        d3.select(this).attr('stroke-width', strokeW('score' in d ? d.score : 100) * 4);
        const n1 = nodeById.get(d.source)!;
        const n2 = nodeById.get(d.target)!;
        let detail = '';
        if ('score' in d) {
          detail = `Similarity: ${d.score}%` + (d.is_reciprocal ? ' (Reciprocal)' : ' (Non-Reciprocal)');
        } else if (d.link_type === 'solid_red') {
          detail = 'Inconsistent Across Domains';
        } else if (d.link_type === 'solid_color') {
          detail = 'Consistent Across Domains';
        } else if (d.link_type === 'dotted_color') {
          detail = 'Consistent, but May Have Missing Domains';
        } else if (d.link_type === 'dotted_gray') {
          detail = 'Non-Reciprocal Connection';
        } else {
          detail = 'Unknown Link Type';
        }
        d3.select(tooltipEl).style('opacity', 1).html(`<strong>${n1.protein_name}</strong> ↔ <strong>${n2.protein_name}</strong><br>${detail}`);
      })
      .on('mousemove', function (event) {
        d3.select(tooltipEl).style('left', event.pageX + 10 + 'px').style('top', event.pageY + 10 + 'px');
      })
      .on('mouseout', function (event, d) {
        d3.select(this).transition().duration(150).attr('stroke-width', strokeW('score' in d ? d.score : 100) * 2);
        d3.select(tooltipEl).style('opacity', 0);
      });

    // NODES
    content
      .append('g')
      .selectAll('path')
      .data(nodes)
      .enter()
      .append('path')
      .attr('d', (d) => arrowPath(d.direction))
      .attr('fill', (d) => nodeColor?.get(d.id)!)
      .attr('transform', (d) => {
        const px = x(d.rel_position);
        const py = y(rowOf(d))! + y.bandwidth() / 2 + margin.top;
        return `translate(${px},${py})`;
      })
      .on('mouseover', function (event, d) {
        d3.select(this).attr('opacity', 0.8);
        d3.select(tooltipEl)
          .style('opacity', 1)
          .html(
            `<strong>Genome:</strong> ${d.genome_name}<br>` +
            `<strong>Protein:</strong> ${d.protein_name}<br>` +
            (d.gene_type ? `<strong>Domain:</strong> ${d.gene_type}<br>` : '') +
            `<strong>Present:</strong> ${d.is_present === false ? 'NO' : 'YES'}<br>` +
            `<strong>Direction:</strong> ${d.direction === 'plus' ? '+' : '-'}<br>` +
            `<strong>Position:</strong> ${d.rel_position}`
          );
      })
      .on('mousemove', function (event) {
        d3.select(tooltipEl).style('left', event.pageX + 10 + 'px').style('top', event.pageY + 10 + 'px');
      })
      .on('mouseout', function () {
        d3.select(this).attr('opacity', 1);
        d3.select(tooltipEl).style('opacity', 0);
      });
  }

  function downloadSVG() {
    // Create a new SVG that will contain both the labels and chart
    const combinedSvg = d3.select(document.createElementNS('http://www.w3.org/2000/svg', 'svg'))
      .attr('width', chartSvgEl.getBoundingClientRect().width + labelSvgEl.getBoundingClientRect().width)
      .attr('height', height);

    // Get the chart SVG content
    const chartSvg = d3.select(chartSvgEl);
    const chartContent = chartSvg.select('g').node() as SVGElement;

    // Get the labels SVG content
    const labelSvg = d3.select(labelSvgEl);
    const labelContent = labelSvg.select('g').node() as SVGElement;

    // Create a group for the chart content and position it
    const chartGroup = combinedSvg.append('g')
      .attr('transform', `translate(${labelWidth}, 0)`);

    // Create a group for the labels and position it
    const labelGroup = combinedSvg.append('g')
      .attr('transform', 'translate(0, 0)');

    // Clone and append the contents
    if (chartContent) chartGroup.node()?.appendChild(chartContent.cloneNode(true));
    if (labelContent) labelGroup.node()?.appendChild(labelContent.cloneNode(true));

    // Serialize and download
    const svgData = new XMLSerializer().serializeToString(combinedSvg.node()!);
    const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(svgBlob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'diagram.svg';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  onMount(draw);
  afterUpdate(draw);
</script>

<!-- Layout: labels fixed on the left, chart scrolls horizontally on the right -->
<div class="wrapper">
  <svg bind:this={labelSvgEl} class="labels"></svg>
  <div class="scroll" style="overflow-x:auto;">
    <svg bind:this={chartSvgEl} class="chart"></svg>
  </div>
</div>
<div bind:this={tooltipEl} class="tooltip"></div>
{#if graph.nodes.length > 0}
  <button on:click={downloadSVG} class="download-btn">Download SVG</button>
{/if}

<style>
  .wrapper {
    display: flex;
    width: 100%;
  }
  .labels {
    flex: 0 0 auto;
  }
  .chart {
    flex: 0 0 auto;
  }
  .scroll {
    flex: 1 1 auto;
  }
  .tooltip {
    position: absolute;
    background: #fff;
    border: 1px solid #999;
    border-radius: 4px;
    padding: 4px 6px;
    font-size: 12px;
    pointer-events: none;
    opacity: 0;
    white-space: nowrap;
  }

  .download-btn {
    margin-left: 40px;
    padding: 6px 12px;
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  .download-btn:hover {
    background-color: #0056b3;
  }
</style>
