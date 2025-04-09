<script lang="ts">
  import { onMount, afterUpdate } from 'svelte';
  import * as d3 from 'd3';

  // Graph payload injected by parent (nodes + links)
  export let graph: {
    nodes: Node[];
    links: Link[];
  };

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
    score: number;       // 0–100
    is_reciprocal: boolean;
  }

  let svgEl: SVGSVGElement;
  const margin = { top: 20, right: 20, bottom: 20, left: 100 };
  const width = 1000;
  const height = 600;

  /* -------------------------------------------------------------
   * Duplicate the first‑genome nodes onto a bottom row so that any
   * GreenTowers ↔ RedValley link only spans **one** row. The duplicate
   * nodes look identical to the originals and carry the same label.
   * ------------------------------------------------------------- */
  function massage(original: typeof graph) {
    if (!original) return { nodes: [], links: [], genomes: [] };

    const genomes = Array.from(new Set(original.nodes.map((n) => n.genome_name)));
    const firstGenome = genomes[0];
    const dupSuffix = '__dup';

    // 1 · duplicate first‑genome nodes
    const nodes: Node[] = [...original.nodes];
    const dupMap = new Map<string, string>(); // original id → dup id

    original.nodes.forEach((n) => {
      if (n.genome_name === firstGenome) {
        const dupId = n.id + dupSuffix;
        dupMap.set(n.id, dupId);
        nodes.push({ ...n, id: dupId, _dup: true });
      }
    });

    // 2 · redirect long‑jump links to the duplicate row
    const genomeOf = new Map(nodes.map((n) => [n.id, n.genome_name]));

    const links: Link[] = original.links.map((l) => {
      const gSrc = genomeOf.get(l.source);
      const gTgt = genomeOf.get(l.target);
      if (!gSrc || !gTgt) return l;

      const rowSrc = genomes.indexOf(gSrc);
      const rowTgt = genomes.indexOf(gTgt);

      if (Math.abs(rowSrc - rowTgt) > 1) {
        // spans middle genome → rewrite one endpoint
        if (gSrc === firstGenome) {
          return { ...l, source: dupMap.get(l.source)! };
        } else {
          return { ...l, target: dupMap.get(l.target)! };
        }
      }
      return l;
    });

    return { nodes, links, genomes };
  }

  function draw() {
    const { nodes, links, genomes } = massage(graph);
    if (!nodes.length) return;

    const svg = d3.select(svgEl);
    svg.selectAll('*').remove();

    const innerW = width - margin.left - margin.right;
    const innerH = height - margin.top - margin.bottom;

    const g = svg
      .attr('width', width)
      .attr('height', height)
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // ---------- scales ----------
    const numRows = genomes.length + 1; // +1 bottom duplicate row
    const y = d3
      .scaleBand<number>()
      .domain(d3.range(numRows))
      .range([0, innerH])
      .padding(0.6);

    const x = d3
      .scaleLinear<number, number>()
      .domain(d3.extent(nodes, (d) => d.rel_position) as [number, number])
      .range([0, innerW]);

    const strokeW = d3.scaleLinear<number, number>().domain([0, 100]).range([0.5, 3]);

    const nodeById = new Map(nodes.map((n) => [n.id, n]));
    const rowOf = (n: Node) => (n._dup ? genomes.length : genomes.indexOf(n.genome_name));

    // ---------- links ----------
    g.append('g')
      .selectAll('line')
      .data(links)
      .enter()
      .append('line')
      .attr('x1', (d) => x(nodeById.get(d.source)!.rel_position))
      .attr('y1', (d) => y(rowOf(nodeById.get(d.source)!))! + y.bandwidth() / 2)
      .attr('x2', (d) => x(nodeById.get(d.target)!.rel_position))
      .attr('y2', (d) => y(rowOf(nodeById.get(d.target)!))! + y.bandwidth() / 2)
      .attr('stroke-width', (d) => strokeW(d.score))
      .attr('stroke-dasharray', (d) => (d.is_reciprocal ? null : '4,4'))
      .attr('stroke', '#444');

    // ---------- nodes ----------
    g.append('g')
      .selectAll('circle')
      .data(nodes)
      .enter()
      .append('circle')
      .attr('cx', (d) => x(d.rel_position))
      .attr('cy', (d) => y(rowOf(d))! + y.bandwidth() / 2)
      .attr('r', 4)
      .attr('fill', '#1f77b4');

    // ---------- genome labels for *every* row ----------
    const yLabels = [...genomes, genomes[0]]; // bottom row label duplicates first genome

    g.append('g')
      .selectAll('text')
      .data(yLabels)
      .enter()
      .append('text')
      .attr('x', -10)
      .attr('y', (_, i) => y(i)! + y.bandwidth() / 2)
      .attr('dy', '0.35em')
      .attr('text-anchor', 'end')
      .style('font-size', '12px')
      .text((d) => d);
  }

  onMount(draw);
  afterUpdate(draw);
</script>

<style>
  svg {
    font-family: sans-serif;
  }
</style>

<svg bind:this={svgEl}></svg>
