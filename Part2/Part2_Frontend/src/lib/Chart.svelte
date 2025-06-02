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
    domain_name?: string;
  };
  export let cutoff: number = 1;

  // Link filter props
  export let showReciprocal = true;
  export let showNonReciprocal = true;
  export let showConsistent = true;
  export let showInconsistent = true;
  export let showPartiallyConsistent = true;

  const dupSuffix = '__dup';

  // Add selection mode state
  let isSelectionMode = false;
  let selectedNodes = new Set<string>();
  let selectedNodesCount = 0;
  let selectedLinks = new Set<string>();
  let isFocused = false;
  let focusedNodes = new Set<string>();
  let focusedLinks = new Set<string>();

  // Add new state variables for context menu and modal
  let showContextMenu = false;
  let contextMenuX = 0;
  let contextMenuY = 0;
  let showPropertiesModal = false;
  let selectedItem: { type: 'node' | 'link', data: any } | null = null;
  let modalSvg: SVGSVGElement;
  let nodeColorMap = new Map<string, string>();

  let showLegend = false;
  let legendPinned = false;
  let panelX = 20;
  let panelY = 20;

  // Calculate dynamic label width based on genome names
  $: labelWidth = Math.min(
    120, // max width
    Math.max(
      80, // min width
      ...graph.genomes.map(name => name.length * 8) // approximate character width
    )
  );


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

  const viewportWidth = 1000;
  // Calculate height based on number of rows (150px per row minimum)
  $: height = (graph.genomes?.length || 0) * 150;
  const margin = { top: 5, right: 20, bottom: 5, left: 10 };
  const arrowHalf = 25;

  const strokeW = d3.scaleLinear<number, number>().domain([0, 100]).range([0.5, 3]);

  function arrowPath(dir: string): string {
    return dir === 'plus'
      ? 'M -25,-15 L 10,-15 L 25,0 L 10,15 L -25,15 Z'
      : 'M 25,-15 L -10,-15 L -25,0 L -10,15 L 25,15 Z';
  }

  /* duplicate first‑genome nodes to bottom row */
  function massage(original: typeof graph) {
    if (!original) return {
      nodes: [] as Node[],
      links: [] as Link[],
      genomes: [] as string[],
      nodeColor: new Map<string, string>()
    };
    const genomes = original.genomes;
    const firstGenome = genomes[0];

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
      if (!gSrc || !gTgt) {
        console.warn('Link has missing genome mapping:', {
          link: l,
          sourceGenome: gSrc,
          targetGenome: gTgt,
          genomeMap: Object.fromEntries(genomeOf)
        });
        return l;
      }
      const rowSrc = genomes.indexOf(gSrc);
      const rowTgt = genomes.indexOf(gTgt);
      if (Math.abs(rowSrc - rowTgt) > 1) {
        // Check if the source/target is already a duplicate
        const sourceNode = nodes.find(n => n.id === l.source);
        const targetNode = nodes.find(n => n.id === l.target);

        if (gSrc === firstGenome && !sourceNode?._dup) {
          const newLink = { ...l, source: dupMap.get(l.source)! };
          console.log('Link transformed for duplication (source):', {
            original: l,
            transformed: newLink,
            sourceGenome: gSrc,
            targetGenome: gTgt,
            rowSrc,
            rowTgt,
            dupMap: Object.fromEntries(dupMap)
          });
          return newLink;
        } else if (gTgt === firstGenome && !targetNode?._dup) {
          const newLink = { ...l, target: dupMap.get(l.target)! };
          console.log('Link transformed for duplication (target):', {
            original: l,
            transformed: newLink,
            sourceGenome: gSrc,
            targetGenome: gTgt,
            rowSrc,
            rowTgt,
            dupMap: Object.fromEntries(dupMap)
          });
          return newLink;
        }
      }
      return l;
    })
    // Exclude links between genes of the same genome
    .filter((l) => {
      const gSrc = genomeOf.get(l.source);
      const gTgt = genomeOf.get(l.target);
      const isSameGenome = gSrc === gTgt;
      if (isSameGenome) {
        console.log('Filtered out same-genome link:', {
          link: l,
          sourceGenome: gSrc,
          targetGenome: gTgt
        });
      }
      return !isSameGenome;
    });

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

    return { nodes, links, genomes, nodeColor, uf };
  }

  // ────────────────────────────────────────────────────────────────
  //  Render
  // ────────────────────────────────────────────────────────────────
  function draw() {
    const { nodes, links, genomes, nodeColor, uf } = massage(graph);
    nodeColorMap = nodeColor;
    if (!nodes.length) return;

    // Create a map of node IDs to their data for quick lookup
    const nodeMap = new Map(nodes.map(node => [node.id, node]));

    // Filter out links that reference non-existent nodes
    const validLinks = links.filter(link => {
        const sourceNode = nodeMap.get(link.source);
        const targetNode = nodeMap.get(link.target);
        return sourceNode && targetNode;
    });

    // Update the graph with only valid links
    graph = {
        ...graph,
        links: validLinks
    };

    // apply cutoff filter
    const visibleLinks = links.filter((l) => {
      // First apply cutoff filter for score-based links
      if ('score' in l && l.score < cutoff) return false;

      // Then apply link type filters
      if ('is_reciprocal' in l) {
        return l.is_reciprocal ? showReciprocal : showNonReciprocal;
      }

      if ('link_type' in l) {
        switch (l.link_type) {
          case 'solid_color':
            return showConsistent;
          case 'solid_red':
            return showInconsistent;
          case 'dotted_color':
            return showPartiallyConsistent;
          case 'dotted_grey':
          case 'dotted_gray':
            return showNonReciprocal;
          default:
            return true;
        }
      }

      return true;
    });

    // Calculate focused nodes and links if in focus mode
    if (isFocused && (selectedNodes.size > 0 || selectedLinks.size > 0)) {
      focusedNodes.clear();
      focusedLinks.clear();

      // Helper function to get both original and duplicated node IDs
      const getNodeAndDup = (nodeId: string) => {
        const node = nodes.find(n => n.id === nodeId);
        if (!node) return [nodeId];

        if (node._dup) {
          // If this is a duplicated node, get the original
          const originalId = nodeId.slice(0, -dupSuffix.length);
          return [nodeId, originalId];
        } else {
          // If this is an original node, check if it has a duplicate
          const dupId = nodeId + dupSuffix;
          const hasDup = nodes.some(n => n.id === dupId);
          return hasDup ? [nodeId, dupId] : [nodeId];
        }
      };

      // Add selected nodes and their CC members
      selectedNodes.forEach(nodeId => {
        const root = uf!.find(nodeId);
        nodes.forEach(n => {
          if (uf!.find(n.id) === root) {
            focusedNodes.add(n.id);
          }
        });
      });

      // Add all links between focused nodes
      visibleLinks.forEach(link => {
        if (focusedNodes.has(link.source) && focusedNodes.has(link.target)) {
          focusedLinks.add(`${link.source}-${link.target}`);
        }
      });

      // Add nodes directly connected to originally selected nodes
      visibleLinks.forEach(link => {
        const sourceIds = getNodeAndDup(link.source);
        const targetIds = getNodeAndDup(link.target);

        // Check if any of the selected nodes (or their duplicates) are involved
        const isSelected = sourceIds.some(id => selectedNodes.has(id)) ||
                          targetIds.some(id => selectedNodes.has(id));

        if (isSelected) {
          // Add all variants of the nodes involved
          sourceIds.forEach(id => focusedNodes.add(id));
          targetIds.forEach(id => focusedNodes.add(id));
          focusedLinks.add(`${link.source}-${link.target}`);
        }
      });

      // Add selected links and their nodes
      selectedLinks.forEach(linkId => {
        const [source, target] = linkId.split('-');
        const sourceIds = getNodeAndDup(source);
        const targetIds = getNodeAndDup(target);

        sourceIds.forEach(id => focusedNodes.add(id));
        targetIds.forEach(id => focusedNodes.add(id));
        focusedLinks.add(linkId);
      });
    }

    // scales
    const numRows = genomes.length > 2 ? genomes.length + 1 : genomes.length; // Updated so no extra line when there are only 2 genomes
    const y = d3.scaleBand<number>().domain(d3.range(numRows)).range([0, height]);
    const xExtent = d3.extent(nodes, (d) => d.rel_position) as [number, number];
    const spacing = 100;
    const chartWidth = (xExtent[1] - xExtent[0]) * spacing + arrowHalf * 2 + margin.left + margin.right;
    const x = d3.scaleLinear<number, number>().domain(xExtent).range([arrowHalf + margin.left + 10, chartWidth - arrowHalf - margin.right - 10]);

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
      .text((d) => {
        // Truncate long genome names
        if (d.length > 15) {
          return d.slice(0, 12) + '...';
        }
        return d;
      });

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
      .attr('x1', (d) => {
        const sourceNode = nodeById.get(d.source);
        if (!sourceNode) {
          console.error('Missing source node:', {
            link: d,
            source: d.source,
            availableNodes: Array.from(nodeById.keys())
          });
          return 0;
        }
        const xBase = x(sourceNode.rel_position);
        return xBase + (sourceNode.direction === 'plus' ? -5 : 5); // Offset based on direction
      })
      .attr('y1', (d) => {
        const sourceNode = nodeById.get(d.source);
        const targetNode = nodeById.get(d.target);
        if (!sourceNode || !targetNode) {
          console.error('Missing node in y1 calculation:', {
            link: d,
            sourceNode: sourceNode ? 'exists' : 'missing',
            targetNode: targetNode ? 'exists' : 'missing',
            availableNodes: Array.from(nodeById.keys())
          });
          return 0;
        }
        const sourceRow = rowOf(sourceNode);
        const targetRow = rowOf(targetNode);
        const yBase = y(sourceRow)! + y.bandwidth() / 2 + margin.top;
        return yBase + (targetRow > sourceRow ? 10 : -10); // Offset by 10 up or down
      })
      .attr('x2', (d) => {
        const targetNode = nodeById.get(d.target);
        if (!targetNode) {
          console.error('Missing target node:', {
            link: d,
            target: d.target,
            availableNodes: Array.from(nodeById.keys())
          });
          return 0;
        }
        const xBase = x(targetNode.rel_position);
        return xBase + (targetNode.direction === 'plus' ? -5 : 5); // Offset based on direction
      })
      .attr('y2', (d) => {
        const sourceNode = nodeById.get(d.source);
        const targetNode = nodeById.get(d.target);
        if (!sourceNode || !targetNode) {
          console.error('Missing node in y2 calculation:', {
            link: d,
            sourceNode: sourceNode ? 'exists' : 'missing',
            targetNode: targetNode ? 'exists' : 'missing',
            availableNodes: Array.from(nodeById.keys())
          });
          return 0;
        }
        const sourceRow = rowOf(sourceNode);
        const targetRow = rowOf(targetNode);
        const yBase = y(targetRow)! + y.bandwidth() / 2 + margin.top;
        return yBase + (targetRow > sourceRow ? -10 : 10); // Offset by 10 up or down
      })
      .attr('stroke-width', (d) => strokeW('score' in d ? d.score : 100) * 2)
      .attr('stroke-dasharray', d => {
        if ('is_reciprocal' in d) return d.is_reciprocal ? null : '4,4';
        if ('link_type' in d) return d.link_type.includes('dotted') ? '4,4' : null;
        return null;
      })
      .attr('stroke', d => {
        if (isFocused && !focusedLinks.has(`${d.source}-${d.target}`)) return '#e6e6e6';
        if (selectedLinks.has(`${d.source}-${d.target}`)) return '#000';
        if ('is_reciprocal' in d) return d.is_reciprocal ? (nodeColorMap.get(d.source) || '#bbb') : '#bbb';
        if ('link_type' in d) {
          if (d.link_type === 'solid_red') return 'red';
          return d.link_type.includes('color') ? (nodeColorMap.get(d.source) || '#bbb') : '#bbb';
        }
        return '#bbb';
      })
      .attr('opacity', d => isFocused && !focusedLinks.has(`${d.source}-${d.target}`) ? 0.3 : 1)
      .style('cursor', isSelectionMode ? 'pointer' : 'default')
      .on('click', function(event, d) {
        if (!isSelectionMode) return;

        const linkId = `${d.source}-${d.target}`;
        if (selectedLinks.has(linkId)) {
          selectedLinks.delete(linkId);
        } else {
          selectedLinks.add(linkId);
        }
        draw();
      })
      .on('mouseover', function (event, d) {
        try {
          d3.select(this).attr('stroke-width', strokeW('score' in d ? d.score : 100) * 4);
          const n1 = nodeById.get(d.source)!;
          const n2 = nodeById.get(d.target)!;

          // Debug logging for link data
          console.log('Link data:', {
            source: d.source,
            target: d.target,
            score: 'score' in d ? d.score : undefined,
            is_reciprocal: 'is_reciprocal' in d ? d.is_reciprocal : undefined,
            link_type: 'link_type' in d ? d.link_type : undefined,
            source_node: n1,
            target_node: n2,
            raw_data: d
          });

          let detail = '';
          if ('score' in d) {
            detail = `Similarity: ${d.score}%` + (d.is_reciprocal ? ' (Reciprocal)' : ' (Non-Reciprocal)');
          } else if (d.link_type === 'solid_red') {
            detail = 'Inconsistent Across Domains';
          } else if (d.link_type === 'solid_color') {
            detail = 'Consistent Across Domains';
          } else if (d.link_type === 'dotted_color') {
            detail = 'Consistent, but May Have Missing Domains';
          } else if (d.link_type === 'dotted_gray' || d.link_type === 'dotted_grey') {
            detail = 'Non-Reciprocal Connection';
          } else {
            detail = 'Unknown Link Type';
          }

          const tooltip = d3.select(tooltipEl);
          tooltip.style('opacity', 1).html(`<strong>${n1.protein_name}</strong> ↔ <strong>${n2.protein_name}</strong><br>${detail}`);
          tooltip.style('left', `${event.clientX + 10}px`).style('top', `${event.clientY + 10}px`);
        } catch (error) {
          console.error('Error in link mouseover handler:', {
            error,
            linkData: d,
            event,
            stack: error.stack
          });
        }
      })
      .on('mousemove', function (event) {
        try {
          d3.select(tooltipEl)
            .style('left', `${event.clientX + 10}px`)
            .style('top', `${event.clientY + 10}px`);
        } catch (error) {
          console.error('Error in link mousemove handler:', {
            error,
            event,
            stack: error.stack
          });
        }
      })
      .on('mouseout', function (event, d) {
        try {
          d3.select(this).transition().duration(150).attr('stroke-width', strokeW('score' in d ? d.score : 100) * 2);
          d3.select(tooltipEl).style('opacity', 0);
        } catch (error) {
          console.error('Error in link mouseout handler:', {
            error,
            linkData: d,
            event,
            stack: error.stack
          });
        }
      })
      .on('contextmenu', function(event, d) {
        handleContextMenu(event, { type: 'link', data: d });
      });

    // NODES
    content
      .append('g')
      .selectAll('path')
      .data(nodes)
      .enter()
      .append('path')
      .attr('d', (d) => arrowPath(d.direction))
      .attr('fill', (d) => {
        if (isFocused && !focusedNodes.has(d.id)) return '#e6e6e6';
        return nodeColorMap.get(d.id) || '#bbb';
      })
      .attr('stroke', (d) => selectedNodes.has(d.id) ? 'black' : 'none')
      .attr('stroke-width', (d) => selectedNodes.has(d.id) ? '2' : '0')
      .attr('opacity', d => {
        if (isFocused && !focusedNodes.has(d.id)) return 0.3;
        return 1;
      })
      .attr('transform', (d) => {
        const px = x(d.rel_position);
        const py = y(rowOf(d))! + y.bandwidth() / 2 + margin.top;
        return `translate(${px},${py})`;
      })
      .style('cursor', isSelectionMode ? 'pointer' : 'default')
      .on('click', function(event, d) {
        if (!isSelectionMode) return;

        // Get both original and duplicated node IDs
        const nodeIds = d._dup ?
          [d.id, d.id.slice(0, -dupSuffix.length)] :
          [d.id, d.id + dupSuffix];

        // Toggle selection for both nodes
        const isSelected = selectedNodes.has(d.id);
        nodeIds.forEach(id => {
          if (isSelected) {
            selectedNodes.delete(id);
          } else {
            selectedNodes.add(id);
          }
        });
        selectedNodesCount = selectedNodes.size;
        draw();
      })
      .on('mouseover', function (event, d) {
        try {
          const currentColor = d3.select(this).attr('fill');
          if (currentColor) {
            const darkerColor = d3.color(currentColor)?.darker(0.3);
            if (darkerColor) {
              d3.select(this).attr('fill', darkerColor.toString());
            }
          }

          // Debug logging for node data
          console.log('Node data:', {
            id: d.id,
            genome_name: d.genome_name,
            protein_name: d.protein_name,
            gene_type: d.gene_type,
            is_present: d.is_present,
            direction: d.direction,
            rel_position: d.rel_position,
            raw_data: d
          });

          // Build tooltip content
          let tooltipContent = `
            <strong>Genome:</strong> ${d.genome_name}<br>
            <strong>Protein:</strong> ${d.protein_name}<br>
            ${d.gene_type ? `<strong>Domain:</strong> ${d.gene_type}<br>` : ''}
            <strong>Present:</strong> ${d.is_present === false ? 'NO' : 'YES'}<br>
            <strong>Direction:</strong> ${d.direction === 'plus' ? '+' : '-'}<br>
            <strong>Position:</strong> ${d.rel_position}
          `;

          // Add domain coordinates if they exist
          const domainCoords = Object.entries(d)
            .filter(([key]) => key.includes('domain') && (key.endsWith('_start') || key.endsWith('_end')))
            .sort(([a], [b]) => a.localeCompare(b));

          if (domainCoords.length > 0) {
            tooltipContent += '<br><br><strong>Domain Coordinates:</strong><br>';
            let currentDomain = '';
            let startValue: number | null = null;
            let endValue: number | null = null;

            domainCoords.forEach(([key, value]) => {
              const parts = key.split('_');
              const domainName = parts[1];
              const coordType = parts[parts.length - 1];

              if (domainName !== currentDomain) {
                if (currentDomain !== '') {
                  tooltipContent += `(${startValue ?? 'N/A'}, ${endValue ?? 'N/A'})<br>`;
                }
                currentDomain = domainName;
                tooltipContent += `${domainName}: `;
                startValue = null;
                endValue = null;
              }

              if (coordType === 'start') {
                startValue = value as number;
              } else if (coordType === 'end') {
                endValue = value as number;
              }
            });

            // Handle the last domain
            if (currentDomain !== '') {
              tooltipContent += `(${startValue ?? 'N/A'}, ${endValue ?? 'N/A'})`;
            }
          }

          d3.select(tooltipEl)
            .style('opacity', 1)
            .style('left', `${event.clientX + 10}px`).style('top', `${event.clientY + 10}px`)
            .html(tooltipContent);
        } catch (error) {
          console.error('Error in node mouseover handler:', {
            error,
            nodeData: d,
            event,
            stack: error.stack
          });
        }
      })
      .on('mousemove', function (event) {
        try {
          d3.select(tooltipEl)
            .style('left', `${event.clientX + 10}px`)
            .style('top', `${event.clientY + 10}px`);
        } catch (error) {
          console.error('Error in node mousemove handler:', {
            error,
            event,
            stack: error.stack
          });
        }
      })
      .on('mouseout', function (event, d) {
        try {
          if (isFocused && !focusedNodes.has(d.id)) {
            d3.select(this).attr('fill', '#e6e6e6');
          } else {
            d3.select(this).attr('fill', nodeColorMap.get(d.id) || '#bbb');
          }
          d3.select(tooltipEl).style('opacity', 0);
        } catch (error) {
          console.error('Error in node mouseout handler:', {
            error,
            nodeData: d,
            event,
            stack: error.stack
          });
        }
      })
      .on('contextmenu', function(event, d) {
        handleContextMenu(event, { type: 'node', data: d });
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

  function toggleSelectionMode() {
    isSelectionMode = !isSelectionMode;
    if (!isSelectionMode) {
      selectedNodes.clear();
      selectedLinks.clear();
      selectedNodesCount = 0;
      isFocused = false;
    }
    draw();
  }

  function applyFocus() {
    if (selectedNodes.size === 0) return;
    isFocused = true;
    draw();
  }

  export function exitFocus() {
    isFocused = false;
    selectedNodes.clear();
    selectedNodesCount = 0;
    draw();
  }

  function handleContextMenu(event: MouseEvent, item: { type: 'node' | 'link', data: any }) {
    event.preventDefault();
    contextMenuX = event.clientX;
    contextMenuY = event.clientY;
    selectedItem = item;
    showContextMenu = true;

    // Add click listener to close menu when clicking outside
    const closeMenuOnOutsideClick = (e: MouseEvent) => {
      const contextMenu = document.querySelector('.context-menu');
      if (contextMenu && !contextMenu.contains(e.target as HTMLElement)) {
        closeContextMenu();
        document.removeEventListener('click', closeMenuOnOutsideClick);
      }
    };

    // Use setTimeout to avoid immediate trigger of the click event
    setTimeout(() => {
      document.addEventListener('click', closeMenuOnOutsideClick);
    }, 0);
  }

  function closeContextMenu() {
    showContextMenu = false;
  }

  function viewProperties() {
    showContextMenu = false;
    showPropertiesModal = true;
  }

  function closeModal() {
    showPropertiesModal = false;
    selectedItem = null;
  }

  function downloadModalSVG() {
    if (!modalSvg || !selectedItem) return;

    // Create a new SVG that will contain both the shape and text
    const combinedSvg = d3.select(document.createElementNS('http://www.w3.org/2000/svg', 'svg'))
      .attr('width', 400)
      .attr('height', 250);

    // Clone the existing SVG content
    const existingContent = modalSvg.querySelector('g');
    if (existingContent) {
      combinedSvg.node()?.appendChild(existingContent.cloneNode(true));
    }

    // Add text elements
    const textGroup = combinedSvg.append('g')
      .attr('transform', 'translate(200, 150)');

    if (selectedItem.type === 'node') {
      textGroup.append('text')
        .attr('x', 0)
        .attr('y', 0)
        .attr('class', 'svg-text')
        .attr('text-anchor', 'middle')
        .text(`Genome: ${selectedItem.data.genome_name}`);

      textGroup.append('text')
        .attr('x', 0)
        .attr('y', 20)
        .attr('class', 'svg-text')
        .attr('text-anchor', 'middle')
        .text(`Protein: ${selectedItem.data.protein_name}`);

      if (selectedItem.data.gene_type) {
        textGroup.append('text')
          .attr('x', 0)
          .attr('y', 40)
          .attr('class', 'svg-text')
          .attr('text-anchor', 'middle')
          .text(`Domain: ${selectedItem.data.gene_type}`);
      }

      textGroup.append('text')
        .attr('x', 0)
        .attr('y', 60)
        .attr('class', 'svg-text')
        .attr('text-anchor', 'middle')
        .text(`Present: ${selectedItem.data.is_present === false ? 'NO' : 'YES'}`);

      textGroup.append('text')
        .attr('x', 0)
        .attr('y', 80)
        .attr('class', 'svg-text')
        .attr('text-anchor', 'middle')
        .text(`Direction: ${selectedItem.data.direction === 'plus' ? '+' : '-'}`);

      textGroup.append('text')
        .attr('x', 0)
        .attr('y', 100)
        .attr('class', 'svg-text')
        .attr('text-anchor', 'middle')
        .text(`Position: ${selectedItem.data.rel_position}`);
    } else {
      // Update the line styling to match the visualization
      const line = combinedSvg.select('line');
      if (line.node()) {
        line
          .attr('stroke', (() => {
            if ('link_type' in selectedItem.data) {
              if (selectedItem.data.link_type === 'solid_red') return 'red';
              return selectedItem.data.link_type.includes('color') ? (nodeColorMap.get(selectedItem.data.source) || '#bbb') : '#bbb';
            }
            return selectedItem.data.is_reciprocal ? (nodeColorMap.get(selectedItem.data.source) || '#bbb') : '#bbb';
          })())
          .attr('stroke-width', strokeW('score' in selectedItem.data ? selectedItem.data.score : 100) * 2)
          .attr('stroke-dasharray', (() => {
            if ('link_type' in selectedItem.data) {
              return selectedItem.data.link_type.includes('dotted') ? '4,4' : null;
            }
            return selectedItem.data.is_reciprocal ? null : '4,4';
          })())
      }

      textGroup.append('text')
        .attr('x', 0)
        .attr('y', 0)
        .attr('class', 'svg-text')
        .attr('text-anchor', 'middle')
        .text(`Source: ${selectedItem.data.source}`);

      textGroup.append('text')
        .attr('x', 0)
        .attr('y', 20)
        .attr('class', 'svg-text')
        .attr('text-anchor', 'middle')
        .text(`Target: ${selectedItem.data.target}`);

      if ('score' in selectedItem.data) {
        textGroup.append('text')
          .attr('x', 0)
          .attr('y', 40)
          .attr('class', 'svg-text')
          .attr('text-anchor', 'middle')
          .text(`Similarity: ${selectedItem.data.score}%`);

        textGroup.append('text')
          .attr('x', 0)
          .attr('y', 60)
          .attr('class', 'svg-text')
          .attr('text-anchor', 'middle')
          .text(`Type: ${selectedItem.data.is_reciprocal ? 'Reciprocal' : 'Non-Reciprocal'}`);
      } else {
        textGroup.append('text')
          .attr('x', 0)
          .attr('y', 40)
          .attr('class', 'svg-text')
          .attr('text-anchor', 'middle')
          .text(`Type: ${selectedItem.data.link_type}`);
      }
    }

    // Add styles
    const style = document.createElementNS('http://www.w3.org/2000/svg', 'style');
    style.textContent = `
      .svg-text {
        font-family: Arial, sans-serif;
        font-size: 12px;
        fill: #333;
      }
    `;
    const firstChild = combinedSvg.node()?.firstChild;
    if (firstChild) {
      combinedSvg.node()?.insertBefore(style, firstChild);
    }

    // Serialize and download
    const svgData = new XMLSerializer().serializeToString(combinedSvg.node()!);
    const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(svgBlob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${selectedItem.type}-properties.svg`;
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
  {#if graph.nodes.length > 0}
    <button
      type="button"
      class="absolute top-2 right-2 w-7 h-7 bg-white border border-slate-200 rounded-lg shadow-sm hover:bg-slate-50 transition-colors cursor-pointer flex items-center justify-center text-slate-600 hover:text-slate-800"
      on:click={() => {
        legendPinned = !legendPinned;
        showLegend = legendPinned;
      }}
      on:mouseenter={() => {
        if (!legendPinned) showLegend = true;
      }}
      on:mouseleave={() => {
        if (!legendPinned) showLegend = false;
      }}
      on:keydown={(e) => {
        if (e.key === 'Enter') {
          legendPinned = !legendPinned;
          showLegend = legendPinned;
        }
      }}
      aria-expanded={showLegend}
      aria-label="Toggle legend"
      class:pinned={legendPinned}
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="16" x2="12" y2="12"/>
        <line x1="12" y1="8" x2="12.01" y2="8"/>
      </svg>
      {#if showLegend}
        <div class="absolute top-full right-0 mt-1 w-72 bg-white border border-slate-200 rounded-lg shadow-lg p-3 z-10">
          <div class="space-y-3">
            <div class="space-y-1.5">
              <h3 class="text-xs font-medium text-slate-800">Nodes</h3>
              <div class="space-y-1.5">
                <div class="flex items-center gap-2">
                  <svg width="32" height="16" viewBox="-25 -15 50 30">
                    <defs>
                      <linearGradient id="rainbow-node" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" style="stop-color:#ff8800"/>
                        <stop offset="20%" style="stop-color:#ffff00"/>
                        <stop offset="40%" style="stop-color:#00ff00"/>
                        <stop offset="60%" style="stop-color:#0088ff"/>
                        <stop offset="80%" style="stop-color:#4400ff"/>
                        <stop offset="100%" style="stop-color:#8800ff"/>
                      </linearGradient>
                    </defs>
                    <path d="M -25,-15 L 10,-15 L 25,0 L 10,15 L -25,15 Z" fill="url(#rainbow-node)" />
                  </svg>
                  <span class="text-xs text-slate-600">Colored: Strongly related nodes</span>
                </div>
                <div class="flex items-center gap-2">
                  <svg width="32" height="16" viewBox="-25 -15 50 30">
                    <path d="M -25,-15 L 10,-15 L 25,0 L 10,15 L -25,15 Z" fill="#7f7f7f" />
                  </svg>
                  <span class="text-xs text-slate-600">Gray: Unrelated nodes</span>
                </div>
                {#if graph.domain_name === "ALL"}
                  <div class="flex items-center gap-2">
                    <svg width="32" height="16" viewBox="-25 -15 50 30">
                      <path d="M -25,-15 L 10,-15 L 25,0 L 10,15 L -25,15 Z" fill="#e6e6e6" />
                    </svg>
                    <span class="text-xs text-slate-600">Light gray: Missing in domain</span>
                  </div>
                {/if}
              </div>
            </div>

            <div class="space-y-1.5">
              <h3 class="text-xs font-medium text-slate-800">Links</h3>
              <div class="space-y-1.5">
                {#if graph.domain_name === "ALL"}
                  <div class="flex items-center gap-2">
                    <svg width="48" height="16" viewBox="0 0 60 20">
                      <!-- Multiple colored segments for rainbow effect, same total length as others -->
                      <line x1="5" y1="10" x2="13" y2="10" stroke="#ff8800" stroke-width="2" />
                      <line x1="13" y1="10" x2="21" y2="10" stroke="#ffdd00" stroke-width="2" />
                      <line x1="21" y1="10" x2="29" y2="10" stroke="#88ff00" stroke-width="2" />
                      <line x1="29" y1="10" x2="37" y2="10" stroke="#00ccff" stroke-width="2" />
                      <line x1="37" y1="10" x2="45" y2="10" stroke="#8866ff" stroke-width="2" />
                    </svg>
                    <div class="text-xs text-slate-600">
                      <div>Colored solid: Consistently</div>
                      <div>reciprocal* across domains</div>
                    </div>
                  </div>
                  <div class="flex items-center gap-2">
                    <svg width="48" height="16" viewBox="0 0 60 20">
                      <line x1="5" y1="10" x2="45" y2="10" stroke="red" stroke-width="2" />
                    </svg>
                    <span class="text-xs text-slate-600">Red: Inconsistent across domains</span>
                  </div>
                  <div class="flex items-center gap-2">
                    <svg width="48" height="16" viewBox="0 0 60 20">
                      <line x1="5" y1="10" x2="13" y2="10" stroke="#ff8800" stroke-width="2" stroke-dasharray="4,4" />
                      <line x1="13" y1="10" x2="21" y2="10" stroke="#ffdd00" stroke-width="2" stroke-dasharray="4,4" />
                      <line x1="21" y1="10" x2="29" y2="10" stroke="#88ff00" stroke-width="2" stroke-dasharray="4,4" />
                      <line x1="29" y1="10" x2="37" y2="10" stroke="#00ccff" stroke-width="2" stroke-dasharray="4,4" />
                      <line x1="37" y1="10" x2="45" y2="10" stroke="#8866ff" stroke-width="2" stroke-dasharray="4,4" />
                    </svg>
                    <span class="text-xs text-slate-600">Colored dotted: Partially consistent</span>
                  </div>
                  <div class="flex items-center gap-2">
                    <svg width="48" height="16" viewBox="0 0 60 20">
                      <line x1="5" y1="10" x2="45" y2="10" stroke="#bbb" stroke-width="2" stroke-dasharray="4,4" />
                    </svg>
                    <span class="text-xs text-slate-600">Gray dotted: Non-reciprocal</span>
                  </div>
                {:else}
                  <div class="flex items-center gap-2">
                    <svg width="48" height="16" viewBox="0 0 60 20">
                      <!-- Multiple colored segments for rainbow effect, same total length as others -->
                      <line x1="5" y1="10" x2="13" y2="10" stroke="#ff8800" stroke-width="2" />
                      <line x1="13" y1="10" x2="21" y2="10" stroke="#ffdd00" stroke-width="2" />
                      <line x1="21" y1="10" x2="29" y2="10" stroke="#88ff00" stroke-width="2" />
                      <line x1="29" y1="10" x2="37" y2="10" stroke="#00ccff" stroke-width="2" />
                      <line x1="37" y1="10" x2="45" y2="10" stroke="#8866ff" stroke-width="2" />
                    </svg>
                    <span class="text-xs text-slate-600">Colored solid: Reciprocal* connection</span>
                  </div>
                  <div class="flex items-center gap-2">
                    <svg width="48" height="16" viewBox="0 0 60 20">
                      <line x1="5" y1="10" x2="45" y2="10" stroke="#bbb" stroke-width="2" stroke-dasharray="4,4" />
                    </svg>
                    <span class="text-xs text-slate-600">Grey dotted: Non-reciprocal</span>
                  </div>
                {/if}
              </div>
            </div>

            <div class="space-y-1">
              <div class="text-xs text-slate-500 border-t border-slate-100 pt-2">
                <p><strong>*Reciprocal:</strong> Both proteins are each other's best match</p>
                <p class="mt-1 text-slate-400">
                  <a href="/help" class="hover:text-slate-600 underline">See help page for detailed explanations</a>
                </p>
              </div>
            </div>
          </div>
        </div>
      {/if}
    </button>
  {/if}
</div>
<div bind:this={tooltipEl} class="tooltip"></div>
<div class="controls">
  {#if graph.nodes.length > 0}
    <button on:click={downloadSVG} class="inline-flex items-center px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors duration-200 cursor-pointer">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mr-2">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
        <polyline points="7 10 12 15 17 10"/>
        <line x1="12" y1="15" x2="12" y2="3"/>
      </svg>
      Download SVG
    </button>
    <button
      on:click={toggleSelectionMode}
      class="inline-flex items-center px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors duration-200 cursor-pointer"
      class:active={isSelectionMode}
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mr-2">
        <path d="M3 3l7.07 16.97 2.51-7.39 7.39-2.51L3 3z"/>
        <path d="M13 13l6 6"/>
      </svg>
      {isSelectionMode ? 'Exit Selection Mode' : 'Enter Selection Mode'}
    </button>
    {#if isSelectionMode && !isFocused}
      <button
        on:click={applyFocus}
        class="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors duration-200 cursor-pointer disabled:bg-green-300 disabled:cursor-not-allowed"
        disabled={selectedNodesCount === 0}
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mr-2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="16"/>
          <line x1="8" y1="12" x2="16" y2="12"/>
        </svg>
        Focus Selected
      </button>
    {/if}
    {#if isFocused}
      <button
        on:click={exitFocus}
        class="inline-flex items-center px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors duration-200 cursor-pointer"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mr-2">
          <line x1="18" y1="6" x2="6" y2="18"/>
          <line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
        Exit Focus
      </button>
    {/if}
  {/if}
</div>

<!-- Add context menu -->
{#if showContextMenu}
  <div
    class="context-menu"
    style="left: {contextMenuX}px; top: {contextMenuY}px"
    on:click|stopPropagation={closeContextMenu}
    on:keydown={(e) => e.key === 'Escape' && closeContextMenu()}
    role="menu"
    tabindex="0"
  >
    <button on:click={viewProperties}>View Properties</button>
  </div>
{/if}

<!-- Add properties modal -->
{#if showPropertiesModal && selectedItem}
  <div class="modal-backdrop" on:click={closeModal} role="dialog" aria-modal="true">
    <div class="modal-content" on:click|stopPropagation on:keydown={(e) => e.key === 'Escape' && closeModal()} role="document">
      <div class="modal-header">
        <h3>{selectedItem.type === 'node' ? 'Node Properties' : 'Link Properties'}</h3>
        <button class="close-button" on:click={closeModal}>×</button>
      </div>

      <div class="modal-body">
        <!-- SVG Preview -->
        <button class="svg-preview" on:click={downloadModalSVG} on:keydown={(e) => e.key === 'Enter' && downloadModalSVG()}>
          {#if selectedItem.type === 'node'}
            <svg bind:this={modalSvg} width="400" height="150">
              <g transform="translate(200,75)">
                <path
                  d={arrowPath(selectedItem.data.direction)}
                  fill={nodeColorMap.get(selectedItem.data.id) || '#bbb'}
                />
              </g>
            </svg>
          {:else}
            <svg bind:this={modalSvg} width="400" height="150">
              <g transform="translate(100,75)">
                <line
                  x1="0"
                  y1="0"
                  x2="200"
                  y2="0"
                  stroke={(() => {
                    if ('link_type' in selectedItem.data) {
                      if (selectedItem.data.link_type === 'solid_red') return 'red';
                      return selectedItem.data.link_type.includes('color') ? (nodeColorMap.get(selectedItem.data.source) || '#bbb') : '#bbb';
                    }
                    return selectedItem.data.is_reciprocal ? (nodeColorMap.get(selectedItem.data.source) || '#bbb') : '#bbb';
                  })()}
                  stroke-width={strokeW('score' in selectedItem.data ? selectedItem.data.score : 100) * 2}
                  stroke-dasharray={(() => {
                    if ('link_type' in selectedItem.data) {
                      return selectedItem.data.link_type.includes('dotted') ? '4,4' : null;
                    }
                    return selectedItem.data.is_reciprocal ? null : '4,4';
                  })()}
                />
              </g>
            </svg>
          {/if}
        </button>

        <!-- Properties -->
        <div class="properties">
          {#if selectedItem.type === 'node'}
            <p><strong>Genome:</strong> {selectedItem.data.genome_name}</p>
            <p><strong>Protein:</strong> {selectedItem.data.protein_name}</p>
            {#if selectedItem.data.gene_type}
              <p><strong>Domain:</strong> {selectedItem.data.gene_type}</p>
            {/if}
            <p><strong>Present:</strong> {selectedItem.data.is_present === false ? 'NO' : 'YES'}</p>
            <p><strong>Direction:</strong> {selectedItem.data.direction === 'plus' ? '+' : '-'}</p>
            <p><strong>Position:</strong> {selectedItem.data.rel_position}</p>

            {#if Object.entries(selectedItem.data).some(([key]) => key.includes('domain'))}
              <div class="domain-coordinates">
                <p><strong>Domain Coordinates:</strong></p>
                {#each Object.entries(selectedItem.data)
                  .filter(([key]) => key.includes('domain') && (key.endsWith('_start') || key.endsWith('_end')))
                  .sort(([a], [b]) => a.localeCompare(b)) as [key, value]}
                  <p>{key}: {value}</p>
                {/each}
              </div>
            {/if}
          {:else}
            <p><strong>Source:</strong> {selectedItem.data.source}</p>
            <p><strong>Target:</strong> {selectedItem.data.target}</p>
            {#if 'score' in selectedItem.data}
              <p><strong>Similarity:</strong> {selectedItem.data.score}%</p>
              <p><strong>Type:</strong> {selectedItem.data.is_reciprocal ? 'Reciprocal' : 'Non-Reciprocal'}</p>
            {:else}
              <p><strong>Type:</strong> {selectedItem.data.link_type}</p>
            {/if}
          {/if}
        </div>
      </div>

      <div class="modal-footer">
        <button class="download-button" on:click={downloadModalSVG}>Download SVG</button>
      </div>
    </div>
  </div>
{/if}

<style>
  .wrapper {
    display: flex;
    width: 100%;
    position: relative;
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
    position: fixed;
    background: #fff;
    border: 1px solid #999;
    border-radius: 4px;
    padding: 4px 6px;
    font-size: 12px;
    pointer-events: none;
    opacity: 0;
    white-space: nowrap;
    z-index: 1000;
  }
  .controls {
    margin: 10px 40px;
    display: flex;
    gap: 10px;
  }

  .control-btn {
    padding: 6px 12px;
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }

  .control-btn:hover {
    background-color: #0056b3;
  }

  .control-btn:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
  }

  .control-btn.active {
    background-color: #28a745;
  }
  .context-menu {
    position: fixed;
    background: white;
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 4px 0;
    box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
    z-index: 1000;
  }
  .context-menu button {
    display: block;
    width: 100%;
    padding: 8px 16px;
    border: none;
    background: none;
    text-align: left;
    cursor: pointer;
  }
  .context-menu button:hover {
    background: #f0f0f0;
  }
  .modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0,0,0,0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
  }
  .modal-content {
    background: white;
    border-radius: 8px;
    padding: 20px;
    width: 90%;
    max-width: 600px;
    max-height: 90vh;
    overflow-y: auto;
  }
  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }
  .close-button {
    background: none;
    border: none;
    font-size: 24px;
    cursor: pointer;
    padding: 0;
    color: #666;
  }
  .modal-body {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }
  .svg-preview {
    display: flex;
    justify-content: center;
    padding: 20px;
    background: #f8f8f8;
    border-radius: 4px;
  }
  .svg-preview:hover {
    background: #f8f8f8;
  }
  .properties {
    display: grid;
    gap: 8px;
  }
  .domain-coordinates {
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid #eee;
  }
  .modal-footer {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
  .download-button {
    padding: 8px 16px;
    background: #007bff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  .download-button:hover {
    background: #0056b3;
  }
  .svg-text {
    font-family: Arial, sans-serif;
    font-size: 12px;
    color: #333;
    text-align: left;
    margin-top: 10px;
    padding: 0 20px;
  }
  .svg-text p {
    margin: 4px 0;
  }

  /* Add styling for pinned legend button */
  .pinned {
    background-color: #e2e8f0 !important;
    border-color: #64748b !important;
  }
</style>
