declare module '*.svelte' {
  import type { ComponentType } from 'svelte';
  const component: ComponentType;
  export default component;
}

interface Node {
  id: string;
  genome_name: string;
  protein_name: string;
  direction: string;
  rel_position: number;
  gene_type: string;
  is_present: boolean;
  [key: string]: any; // For domain-specific properties
}

interface Link {
  source: string;
  target: string;
  score: number;
  is_reciprocal: boolean;
}

interface GraphData {
  nodes: Node[];
  links: Link[];
}

interface FileUploadEvent extends Event {
  target: HTMLInputElement;
} 