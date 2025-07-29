import pandas as pd
from io import BytesIO
from flask import jsonify
import json
import argparse
import sys
from parsing.file_utils import parse_matrix_data
from core.matrix_file import MatrixFile
from core.coordinate_file import CoordinateFile
from core.config import FileProcessingConfig
from parsing.graph_utils import add_nodes, add_links

def parse_filenames(file_names):
    domains = []
    for name in file_names:
        # Split by underscore and get the last part
        parts = name.split('_')
        if len(parts) > 1:
            # Get the last part and remove the extension
            domain_name = parts[-1].split('.')[0]
            domains.append(domain_name)

    return domains


def create_output(matrix_data, coords, domain):
    genomes = coords['genome'].unique().tolist()  # Convert numpy array to list
    nodes = add_nodes(coords, cutoff_index=matrix_data['df_only_cutoffs'].index, include_gene_type=True, include_domains=True)
    links, domain_connections, domain_genes = add_links(
        matrix_data['df_only_cutoffs'],
        matrix_data['row_max'],
        matrix_data['col_max'],
        coords,
        genomes=genomes,
        domain=domain,
        return_connections=True
    )
    return nodes, links, domain_connections, domain_genes, matrix_data['df_only_cutoffs'].index

def combine_graphs(all_domain_connections, all_domain_genes, domains):
    #for each connection in domain 1 check if the connection exists in domains 2/3 and if those are reciprocal
        #genomeA_gene1-genomeB_gene2 --> domain 1
        #genomeB_gene2-genomeA_gene1 --> domain 2
    #for each connection in domain 2:
        #check if connection has already been parsed through

    # Collect all unique connections across all domains
    all_keys = set()
    unique_links = set()
    # print(all_keys)
    # print(unique_links)
    for domain_dict in all_domain_connections:
        for key, value in domain_dict.items():
            all_keys.add(key)
            # unique_links.add((key, value)) # ("src_tgt", {'TIR': True})
            for key_1, key_2 in value.items():
                 unique_links.add((key, key_1, key_2)) # ("src_tgt", 'TIR', True})
            #         unique_links.add((key, item)) # ("source_target", "TIR")

    combined = []
    num_domains = len(domains)

    for key in all_keys:
        source, target = key.split('#', 1)
        reverse_key = f"{target}#{source}"
        # Check if this key exists in all domain dicts

        present_in_domains = [
            any((u_key == key or u_key == reverse_key) and dom_name == domain
            for u_key, dom_name, dom_bool in unique_links)
            for domain in domains
            # (pair in unique_links) or (reverse_key_pairs[i] in unique_links)
            # for i, pair in enumerate(key_domain_pairs)
        ]

        link_type = ""

        if not all(present_in_domains):
            # Check if connection is reciprocal in domains where it exists AND nodes don't exist in domains where connection is missing
            if all(dom_bool for u_key, _, dom_bool in unique_links if u_key == key or u_key == reverse_key):
                # Check if both nodes exist in any domain where the connection is missing
                if any(source in all_domain_genes[i][domains[i]] and target in all_domain_genes[i][domains[i]]
                      for i, present in enumerate(present_in_domains) if not present):
                    link_type = "solid_red"
                else:
                    link_type = "solid_color"
            # At least one reciprocal
            elif any(dom_bool for u_key, _, dom_bool in unique_links if u_key == key or u_key == reverse_key):
                if any(source in all_domain_genes[i][domains[i]] and target in all_domain_genes[i][domains[i]]
                      for i, present in enumerate(present_in_domains) if not present):
                    link_type = "solid_red"
                else:
                    link_type = "dotted_color"
            else:
                link_type = "dotted_grey"
        else:
            if all(dom_bool for u_key, _, dom_bool in unique_links if u_key == key or u_key == reverse_key):
                link_type = "solid_color"
            elif any(dom_bool for u_key, _, dom_bool in unique_links if u_key == key or u_key == reverse_key):
                link_type = "dotted_color"
            else:
                link_type = "dotted_grey"
        
        # # Optionally, collect which domains it's missing from
        # # missing_domains = [i for i, present in enumerate(present_in_domains) if not present]

        # # You can also merge the domain info if needed
        domain_info = {}
        for i, domain_dict in enumerate(all_domain_connections):
            if key in domain_dict:
                domain_info.update(domain_dict[key])

        combined.append({
            "source": source,
            "target": target,
            "link_type": link_type
            # Change to 1 enum with the different types of connection possible: "Solid Red", "Solid Color", "Dotted Color", "Dotted Gray"
        })
    # print(combined)

    return combined

def domain_parse(matrix_files, coord_file, file_names):
    """
    Parse domain-specific matrix files and coordinate file using both file_utils and data_structures.
    
    Args:
        matrix_files: List of BytesIO objects containing matrix file data
        coord_file: BytesIO object containing coordinate file data
        file_names: List of filenames for domain identification
    
    Returns:
        list: List of graph outputs for each domain plus combined graph
    """
    # Create configuration for enhanced validation
    config = FileProcessingConfig(
        validation_mode="domain",
        parse_comma_separated_numbers=True,
        clean_whitespace=True,
        normalize_orientations=True,
        handle_missing_values=True
    )
    
    # Use data_structures for enhanced coordinate file validation and processing
    coord_data_file = CoordinateFile(coord_file, config)
    coord_data_file.load_data()
    
    # Validate coordinate file with enhanced validation
    if not coord_data_file.validate():
        raise ValueError(f"Coordinate file validation failed: {', '.join(coord_data_file.validation_errors)}")
    
    # Clean coordinate data with enhanced cleaning and domain columns
    coords = coord_data_file.clean_with_domains()
    domains = parse_filenames(file_names)
    genomes = coords['genome'].unique().tolist()

    all_outputs = {}

    genomes_output = []
    all_domain_connections = []
    all_domain_genes = []
    total_genomes = set()
    total_gene_list = []

    for idx, matrix_file in enumerate(matrix_files, 1):
        # Use data_structures for enhanced matrix validation
        matrix_data_file = MatrixFile(matrix_file, config)
        matrix_data_file.load_data()
        
        # Validate matrix file with enhanced validation
        if not matrix_data_file.validate():
            raise ValueError(f"Matrix file {idx} validation failed: {', '.join(matrix_data_file.validation_errors)}")
        
        # Clean matrix data with enhanced cleaning
        matrix_data_file.clean()
        
        graph_output = {"domain_name": domains[idx - 1]}
        matrix_file.seek(0)
        nodes, links, domain_connections, domain_genes, total_gene_list = create_output(parse_matrix_data(matrix_file, genomes, coords), coords, domains[idx - 1])
        all_domain_connections.append(domain_connections)
        all_domain_genes.append(domain_genes)
        total_genomes.update(genomes)
        graph_output["genomes"] = genomes
        graph_output["nodes"] = nodes
        graph_output["links"] = links
        genomes_output.append(graph_output)

    
    #print(total_genomes)

    domain_graph_nodes = add_nodes(coords, cutoff_index=total_gene_list, include_gene_type=True, include_domains=True)
    for node in domain_graph_nodes:
        # Check if the node is present in all domain graphs
        node["is_present"] = any(
            any(n["id"] == node["id"] and n["is_present"] for n in graph["nodes"])
            for graph in genomes_output
        )
    domain_graph = {
        "domain_name": "ALL",
        "genomes": list(total_genomes),
        "nodes": domain_graph_nodes,
        "links": combine_graphs(all_domain_connections, all_domain_genes, domains)
    }

    genomes_output.append(domain_graph)

    return genomes_output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Parse matrix and coordinate files for genome visualization')
    parser.add_argument('matrix_files', type=str, nargs='+', help='Path(s) to 2 or 3 matrix Excel files')
    parser.add_argument('coord_file', type=str, help='Path to the coordinate Excel file')
    parser.add_argument('--output', '-o', type=str, help='Output JSON file path (optional, defaults to stdout)')

    args = parser.parse_args()

    # Ensure 2 or 3 matrix files are provided
    if not (2 <= len(args.matrix_files) <= 3):
        print("Error: You must provide 2 or 3 matrix files.", file=sys.stderr)
        sys.exit(1)

    try:
        # Open matrix files and coordinate file
        matrix_files = [open(f, 'rb') for f in args.matrix_files]
        file_names = [f.name for f in matrix_files]
        with open(args.coord_file, 'rb') as coord_file:
            result_obj = domain_parse(matrix_files, coord_file, file_names)
            output_json = json.dumps(result_obj, indent=2)

            if args.output:
                with open(args.output, 'w') as f:
                    f.write(output_json)
                print(f"Results written to {args.output}")
            else:
                print(output_json)

        # Close matrix files
        for f in matrix_files:
            f.close()

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)