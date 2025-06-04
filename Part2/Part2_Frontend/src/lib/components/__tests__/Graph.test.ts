import { render } from '@testing-library/svelte';
import { describe, it, expect, vi } from 'vitest';
import Graph from '../Graph.svelte';

describe('Graph', () => {
  const mockData = {
    nodes: [
      { id: 'node1', genome_name: 'genome1', is_present: true },
      { id: 'node2', genome_name: 'genome2', is_present: true }
    ],
    links: [
      { source: 'node1', target: 'node2', score: 0.8, is_reciprocal: true }
    ]
  };

  it('renders graph container', () => {
    const { getByTestId } = render(Graph, { data: mockData });
    expect(getByTestId('graph-container')).toBeInTheDocument();
  });

  it('renders nodes', () => {
    const { getByTestId } = render(Graph, { data: mockData });
    const nodes = getByTestId('graph-container').querySelectorAll('.node');
    expect(nodes.length).toBe(mockData.nodes.length);
  });

  it('renders links', () => {
    const { getByTestId } = render(Graph, { data: mockData });
    const links = getByTestId('graph-container').querySelectorAll('.link');
    expect(links.length).toBe(mockData.links.length);
  });

  it('handles empty data', () => {
    const { getByTestId } = render(Graph, { data: { nodes: [], links: [] } });
    const container = getByTestId('graph-container');
    expect(container.querySelectorAll('.node').length).toBe(0);
    expect(container.querySelectorAll('.link').length).toBe(0);
  });

  it('updates when data changes', async () => {
    const { getByTestId, component } = render(Graph, { data: mockData });
    
    const newData = {
      nodes: [...mockData.nodes, { id: 'node3', genome_name: 'genome3', is_present: true }],
      links: [...mockData.links]
    };
    
    component.$set({ data: newData });
    
    const nodes = getByTestId('graph-container').querySelectorAll('.node');
    expect(nodes.length).toBe(newData.nodes.length);
  });
}); 