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
  export let cutoff: number = 0;

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
      ? 'M -40,-10 L 0,-10 L 0,10 L -40,10 Z M 0,-20 L 40,0 L 0,20 Z'
      : 'M 40,-10 L 0,-10 L 0,10 L 40,10 Z M 0,-20 L -40,0 L 0,20 Z';
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
    original.nodes.forEach((n) => {
      if (n.genome_name === firstGenome) {
        const dupId = n.id + dupSuffix;
        dupMap.set(n.id, dupId);
        nodes.push({ ...n, id: dupId, _dup: true });
      }
    });

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
      if (l.is_reciprocal) {
        uf.union(l.source, l.target);
      }
    });

    // Map CCs to colors
    const componentRoots = new Set(nodes.map((n) => uf.find(n.id)));
    // const colorScale = d3.scaleOrdinal([...d3.schemeSet3]).domain([...componentRoots]);
    const componentSize = new Map([...componentRoots].map((root) => [root, 0]));
    nodes.forEach((n) => {
      const root = uf.find(n.id);
      componentSize.set(root, (componentSize.get(root) || 0) + 1);
    });
    const nonSingletonRoots = [...componentRoots].filter((root) => componentSize.get(root)! > 1);
    const colorScale = d3.scaleOrdinal([...d3.schemeSet3]).domain(nonSingletonRoots);
    // Gray-out CCs of size 1
    const nodeColor = new Map(
      nodes.map((n) => {
      const root = uf.find(n.id);
      return [n.id, componentSize.get(root) === 1 ? '#ccc' : colorScale(root)];
      })
    );
    // const nodeColor = new Map(nodes.map((n) => [n.id, colorScale(uf.find(n.id))!]));

    return { nodes, links, genomes, nodeColor };
  }

  // ────────────────────────────────────────────────────────────────
  //  Render
  // ────────────────────────────────────────────────────────────────
  function draw() {
    const { nodes, links, genomes, nodeColor } = massage(graph);
    if (!nodes.length) return;

    // apply cutoff filter
    const visibleLinks = links.filter((l) => l.score >= cutoff);

    // scales
    const numRows = genomes.length + 1;
    const y = d3.scaleBand<number>().domain(d3.range(numRows)).range([0, height - margin.top - margin.bottom]).padding(0.6);
    const xExtent = d3.extent(nodes, (d) => d.rel_position) as [number, number];
    const spacing = 120;
    const chartWidth = Math.max(viewportWidth, (xExtent[1] - xExtent[0]) * spacing + arrowHalf * 2 + margin.left + margin.right);
    const x = d3.scaleLinear<number, number>().domain(xExtent).range([arrowHalf + margin.left, chartWidth - arrowHalf - margin.right]);

    const nodeById = new Map(nodes.map((n) => [n.id, n]));
    const rowOf = (n: Node) => (n._dup ? genomes.length : genomes.indexOf(n.genome_name));

    // ── LABELS ──
    const labelSvg = d3.select(labelSvgEl).attr('width', labelWidth).attr('height', height);
    labelSvg.selectAll('*').remove();
    const yLabels = [...genomes, genomes[0]];
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
      .attr('stroke-width', (d) => strokeW(d.score))
      .attr('stroke-dasharray', (d) => (d.is_reciprocal ? null : '4,4'))
      .attr('stroke', (d) => (d.is_reciprocal ? nodeColor?.get(d.source)! : '#bbb'))
      .on('mouseover', function (event, d) {
        d3.select(this).transition().duration(150).attr('stroke-width', strokeW(d.score) * 2);
        const n1 = nodeById.get(d.source)!;
        const n2 = nodeById.get(d.target)!;
        d3.select(tooltipEl)
          .style('opacity', 1)
          .html(
            `<strong>${n1.protein_name}</strong> ↔ <strong>${n2.protein_name}</strong><br>` +
              `Similarity: ${d.score}%` + (d.is_reciprocal ? ' (reciprocal)' : ' (non‑reciprocal)')
          );
      })
      .on('mousemove', function (event) {
        d3.select(tooltipEl).style('left', event.pageX + 10 + 'px').style('top', event.pageY + 10 + 'px');
      })
      .on('mouseout', function (event, d) {
        d3.select(this).transition().duration(150).attr('stroke-width', strokeW(d.score));
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
</style>
