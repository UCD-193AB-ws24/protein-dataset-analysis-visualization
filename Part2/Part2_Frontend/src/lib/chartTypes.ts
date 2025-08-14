export interface Node {
  id: string;
  genome_name: string;
  protein_name: string;
  direction: string;   // "plus" | "minus"
  rel_position: number;
  is_present?: boolean;
  gene_type?: string;
  _dup?: boolean; // internal flag for duplicated bottom‑row copy
}

export interface Graph {
  genomes: string[];
  nodes: Node[];
  links: Link[];
  domain_name?: string;
}

export type ScoreLink = {
  source: string;
  target: string;
  score: number;
  is_reciprocal: boolean;
};

export type CompareLink = {
  source: string;
  target: string;
  link_type: string; // "solid_color" | "dotted_grey" | etc.
};

export type Link = ScoreLink | CompareLink;
