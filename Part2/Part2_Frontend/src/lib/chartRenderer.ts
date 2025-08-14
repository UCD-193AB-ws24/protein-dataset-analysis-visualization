import { massage } from './chartDataProcessor';
import type { Graph, Node } from './chartTypes';
import * as d3 from 'd3';

const dupSuffix = '__dup';


export let cutoff: number = 25;

// Link filter props
export let showReciprocal = true;
export let showNonReciprocal = true;
export let showConsistent = true;
export let showInconsistent = true;
export let showPartiallyConsistent = true;

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
let selectedItem: { type: 'node' | 'link', data: any } | null = null;
let nodeColorMap = new Map<string, string>();

const margin = { top: 5, right: 20, bottom: 5, left: 10 };
const arrowHalf = 25;

export const strokeW = d3.scaleLinear<number, number>().domain([0, 100]).range([0.5, 3]);

export function arrowPath(dir: string): string {
    return dir === 'plus'
        ? 'M -25,-15 L 10,-15 L 25,0 L 10,15 L -25,15 Z'
        : 'M 25,-15 L -10,-15 L -25,0 L -10,15 L 25,15 Z';
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

export function closeContextMenu() {
    showContextMenu = false;
}


// ────────────────────────────────────────────────────────────────
//  Render
// ────────────────────────────────────────────────────────────────
export function draw(graph: Graph, labelSvgEl: SVGSVGElement, chartSvgEl: SVGSVGElement, tooltipEl: HTMLDivElement) {
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
    const height = (graph.genomes?.length || 0) * 150;
    const y = d3.scaleBand<number>().domain(d3.range(numRows)).range([0, height]);
    const xExtent = d3.extent(nodes, (d) => d.rel_position) as [number, number];
    const spacing = 100;
    const chartWidth = (xExtent[1] - xExtent[0]) * spacing + arrowHalf * 2 + margin.left + margin.right;
    const x = d3.scaleLinear<number, number>().domain(xExtent).range([arrowHalf + margin.left + 10, chartWidth - arrowHalf - margin.right - 10]);
    const labelWidth = Math.min(
        120, //max width
        Math.max(
            80, //min width
            ...genomes.map(name => name.length * 8) //approximate character width
        )
    );

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
            draw(graph, labelSvgEl, chartSvgEl, tooltipEl);
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
            } catch (error: any) {
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
            } catch (error: any) {
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
            } catch (error: any) {
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
            draw(graph, labelSvgEl, chartSvgEl, tooltipEl);
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
                    ${d.gene_type ? `<strong>Gene Type:</strong> ${d.gene_type}<br>` : ''}
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
            } catch (error: any) {
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
            } catch (error: any) {
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
            } catch (error: any) {
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