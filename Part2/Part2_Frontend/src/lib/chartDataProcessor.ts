import * as d3 from 'd3';
import UnionFind from '$lib/UnionFind';
import type { Graph, Node, Link } from './chartTypes';

const dupSuffix = '__dup';


/ duplicate first‑genome nodes to bottom row */
export function massage(original: Graph) {
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

    // Keep the original link
    const originalLink = { ...l };

    // If we need to duplicate (more than 2 genomes and first genome is involved)
    if (genomes.length > 2) {
      const rowSrc = genomes.indexOf(gSrc);
      const rowTgt = genomes.indexOf(gTgt);
      
      if (Math.abs(rowSrc - rowTgt) > 1) {
        // Check if the source/target is already a duplicate
        const sourceNode = nodes.find(n => n.id === l.source);
        const targetNode = nodes.find(n => n.id === l.target);
        
        if (gSrc === firstGenome && !sourceNode?._dup) {
          return { ...l, source: dupMap.get(l.source)! };
        } else if (gTgt === firstGenome && !targetNode?._dup) {
          return { ...l, target: dupMap.get(l.target)! };
        }
      }
    }

    return originalLink;
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
  // Grey-out CCs not associated with colorRoots
  const nodeColor = new Map(
    nodes.map((n) => {
      if (n.is_present === false) return [n.id, '#e6e6e6']

      const root = uf.find(n.id);
      return [n.id, colorRoots.includes(root) ? colorScale(root) : '#7f7f7f'];
    })
  );

  return { nodes, links, genomes, nodeColor, uf };
}