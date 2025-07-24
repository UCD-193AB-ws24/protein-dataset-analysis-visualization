import pandas as pd
from io import BytesIO
from flask import jsonify
from file_utils import (
    parse_matrix_data
)
from data_structures import (
    MatrixFile, 
    CoordinateFile, 
    FileProcessingConfig,
)


def add_nodes(coords):
    nodes = []

    for i in range(len(coords)):
        nodes.append({
            "id" : coords['name'][i],
            "genome_name": coords['genome'][i],
            "protein_name": coords['protein_name'][i],
            "direction": coords['orientation'][i],
            "rel_position": int(coords['rel_position'][i]),
        })

    return nodes

def add_links(df_only_cutoffs, row_max, col_max, coords):
    links = []
    
    # Create a mapping of gene names to their genomes
    gene_to_genome = dict(zip(coords['name'], coords['genome']))

    for row in df_only_cutoffs.index:
        for col in df_only_cutoffs.columns:
            # Skip links between genes in the same genome using the mapping
            if gene_to_genome.get(row) == gene_to_genome.get(col):
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
                continue  # skip non-max values

            links.append({
                "source": source,
                "target": target,
                "score": float(df_only_cutoffs.at[row, col]),
                "is_reciprocal": reciprocal_max
            })

    return links


def create_output(matrix_data, coords):
    output = {"genomes": coords['genome'].unique().tolist()}
    output["nodes"] = add_nodes(coords)
    output["links"] = add_links(matrix_data['df_only_cutoffs'], matrix_data['row_max'], matrix_data['col_max'], coords)
    return output


def parse_matrix(matrix_file, coord_file):
    """
    Parse matrix and coordinate files using both file_utils and data_structures.
    
    Args:
        matrix_file: BytesIO object containing matrix file data
        coord_file: BytesIO object containing coordinate file data
    
    Returns:
        dict: Graph data with nodes and links
    """
    # Create configuration for enhanced validation
    config = FileProcessingConfig(
        validation_mode="general",
        parse_comma_separated_numbers=True,
        clean_whitespace=True,
        normalize_orientations=True,
        handle_missing_values=True
    )
    
    # Use data_structures for enhanced validation and processing
    coord_data_file = CoordinateFile(coord_file, config)
    coord_data_file.load_data()
    
    # Validate coordinate file with enhanced validation
    if not coord_data_file.validate():
        raise ValueError(f"Coordinate file validation failed: {', '.join(coord_data_file.validation_errors)}")
    
    # Clean coordinate data with enhanced cleaning
    coords = coord_data_file.clean()
    
    # Use data_structures for matrix validation
    matrix_data_file = MatrixFile(matrix_file, config)
    matrix_data_file.load_data()
    
    # Validate matrix file with enhanced validation
    if not matrix_data_file.validate():
        raise ValueError(f"Matrix file validation failed: {', '.join(matrix_data_file.validation_errors)}")
    
    # Clean matrix data with enhanced cleaning
    matrix_df = matrix_data_file.clean()
    
    # Use file_utils for the core processing logic
    matrix_data = parse_matrix_data(matrix_file, coords['genome'].unique().tolist(), coords)
    
    return create_output(matrix_data, coords)


if __name__ == "__main__":
    import argparse
    import sys
    import json

    parser = argparse.ArgumentParser(description='Parse matrix and coordinate files for genome visualization')
    parser.add_argument('matrix_file', type=str, help='Path to matrix Excel file')
    parser.add_argument('coord_file', type=str, help='Path to the coordinate Excel file')
    parser.add_argument('--output', '-o', type=str, help='Output JSON file path (optional, defaults to stdout)')

    args = parser.parse_args()

    try:
        # Open matrix file and coordinate file
        with open(args.matrix_file, 'rb') as matrix_file, open(args.coord_file, 'rb') as coord_file:
            result_obj = parse_matrix(matrix_file, coord_file)
            output_json = json.dumps(result_obj, indent=2)

            if args.output:
                with open(args.output, 'w') as f:
                    f.write(output_json)
                print(f"Results written to {args.output}")
            else:
                print(output_json)

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)