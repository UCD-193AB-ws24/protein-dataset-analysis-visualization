import pandas as pd


def add_nodes(coords, cutoff_index=None, include_gene_type=False, include_domains=False):
    """
    Create node dictionaries for graph output.
    Args:
        coords: DataFrame with coordinate data
        cutoff_index: Optional set or list of present gene names (for is_present)
        include_gene_type: Whether to include gene_type in node
        include_domains: Whether to include domain columns in node
    Returns:
        List of node dicts
    """
    nodes = []
    for i in range(len(coords)):
        node_data = {
            "id": coords['name'][i],
            "genome_name": coords['genome'][i],
            "protein_name": coords['protein_name'][i],
            "direction": coords['orientation'][i],
            "rel_position": int(coords['rel_position'][i]),
        }
        if include_gene_type and 'gene_type' in coords.columns:
            node_data["gene_type"] = coords['gene_type'][i]
        if cutoff_index is not None:
            node_data["is_present"] = coords['name'][i] in cutoff_index
        if include_domains:
            domain_cols = [col for col in coords.columns if 'domain' in col]
            for col in domain_cols:
                if col.endswith('_start') or col.endswith('_end'):
                    value = coords[col][i]
                    node_data[col] = None if pd.isna(value) else value
        nodes.append(node_data)
    return nodes


def add_links(df_only_cutoffs, row_max, col_max, coords, genomes=None, domain=None, return_connections=False):
    """
    Create link dictionaries for graph output.
    Args:
        df_only_cutoffs: DataFrame of cutoff-filtered matrix
        row_max, col_max: DataFrames of row/col maxes
        coords: DataFrame with coordinate data
        genomes: Optional list of genome names (for domain case)
        domain: Optional domain name (for domain case)
        return_connections: If True, also return domain_connections and all_genes
    Returns:
        List of link dicts (and optionally domain_connections, all_genes)
    """
    links = []
    domain_connections = {} if return_connections else None
    all_genes = {} if return_connections and domain else None
    gene_to_genome = dict(zip(coords['name'], coords['genome']))
    for row in df_only_cutoffs.index:
        for col in df_only_cutoffs.columns:
            # Optionally skip links between genes in the same genome
            if genomes and (gene_to_genome.get(row) == gene_to_genome.get(col)):
                continue
            is_col_max = pd.notna(col_max.at[row, col])
            is_row_max = pd.notna(row_max.at[row, col])
            if is_row_max and is_col_max:
                source = row
                target = col
                reciprocal_max = True
            elif is_row_max:
                source = row
                target = col
                reciprocal_max = False
            elif is_col_max:
                source = col
                target = row
                reciprocal_max = False
            else:
                continue
            if return_connections and domain:
                domain_connections[f'{source}#{target}'] = {domain: reciprocal_max}
            links.append({
                "source": source,
                "target": target,
                "score": float(df_only_cutoffs.at[row, col]),
                "is_reciprocal": reciprocal_max
            })
    if return_connections and domain:
        all_genes[domain] = df_only_cutoffs.index.tolist()
        return links, domain_connections, all_genes
    return links 