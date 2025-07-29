import pandas as pd
from io import BytesIO
from flask import jsonify
from parsing.file_utils import parse_matrix_data
from core.matrix_file import MatrixFile
from core.coordinate_file import CoordinateFile
from core.config import FileProcessingConfig
from parsing.graph_utils import create_output


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