import pandas as pd
from io import BytesIO
from flask import jsonify
from file_utils import (
    read_file, 
    validate_dataframe_basic, 
    validate_dataframe_structure,
    validate_coordinate_data_types,
    validate_matrix_coordinate_mapping
)


def validate_coordinate_dataframe_basic(df):
    if df.empty:
        raise ValueError("The coordinate file is empty")
        
    # Clean column names by stripping whitespace
    df.columns = df.columns.str.strip()
        
    required_columns = ['name', 'protein_name', 'genome', 'position', 'orientation']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
        
    if df['name'].isnull().any():
        raise ValueError("Found empty values in the name column")
        
    if df['position'].isnull().any():
        raise ValueError("Found empty values in the position column")
        
    if df['orientation'].isnull().any():
        raise ValueError("Found empty values in the orientation column")

def process_name_field(df):
    try:
        if df['protein_name'].isnull().any() or df['genome'].isnull().any():
            raise ValueError("Some names don't follow the expected format (should contain '_')")
            
        return df
    except Exception as e:
        raise ValueError(f"Error processing name field: {str(e)}")

def calculate_relative_positions(df):
    try:
        df['rel_position'] = df.groupby('genome')['position'].rank(method='first').astype(int)
        return df
    except Exception as e:
        raise ValueError(f"Error calculating relative positions: {str(e)}")

def parse_coordinates(coord_file):
    try:
        df = read_file(coord_file, 'coordinate')
        # Clean column names by stripping whitespace
        df.columns = df.columns.str.strip()
        
        # Clean up spaces in all string columns
        for col in df.columns:
            if df[col].dtype == "object":
                df[col] = df[col].astype(str).str.strip()
        
        # Validate basic structure
        validate_coordinate_dataframe_basic(df)
        
        # Validate data types
        validate_coordinate_data_types(df)
        
        # Process name field
        df = process_name_field(df)
        
        # Calculate relative positions
        df = calculate_relative_positions(df)
        
        # Return only the required columns in the specified order
        required_columns = ['name', 'genome', 'protein_name', 'position', 'rel_position', 'orientation']
        if not all(col in df.columns for col in required_columns):
            raise ValueError("Missing one or more required columns after processing")
            
        return df[required_columns]
        
    except pd.errors.EmptyDataError:
        raise ValueError("The coordinate file is empty or cannot be read")
    except Exception as e:
        if not isinstance(e, ValueError):  # Don't wrap ValueError as it's already formatted
            raise ValueError(f"Error processing coordinate file: {str(e)}")
        raise


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
    processed_pairs = set()  # Keep track of processed gene pairs
    
    # Create a mapping of gene names to their genomes
    gene_to_genome = dict(zip(coords['name'], coords['genome']))

    for row in df_only_cutoffs.index:
        for col in df_only_cutoffs.columns:
            # Skip if we've already processed this pair of genes
            pair = tuple(sorted([row, col]))
            if pair in processed_pairs:
                continue
                
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
            
            # Mark this pair as processed
            processed_pairs.add(pair)

    return links

def validate_dataframe_basic(df):
    if df.empty:
        raise ValueError("The matrix file is empty")
    if len(df.columns) < 2 or len(df.index) < 2:
        raise ValueError("Matrix must have at least 2 rows and 2 columns")
    if len(df.columns) == 0:
        raise ValueError("Matrix file must have at least one column for index")

def validate_dataframe_structure(df):
    if df.index.duplicated().any():
        raise ValueError("Matrix contains duplicate row identifiers")
    if df.columns.duplicated().any():
        raise ValueError("Matrix contains duplicate column names")
    if df.empty:
        raise ValueError("Matrix is empty after removing NA values")
    if not df.dtypes.apply(lambda x: pd.api.types.is_numeric_dtype(x)).all():
        raise ValueError("Matrix contains non-numeric values")


def prepare_dataframe(matrix_file):
    print("Parsing matrix file...")
    df = read_file(matrix_file, 'matrix')
    validate_dataframe_basic(df)
    
    df = df.reset_index(drop=True)
    df = df.set_index(df.columns[0])
    df.index.name = None
    
    df = df.dropna(how='all')
    df = df.dropna(axis=1, how='all')
    
    validate_dataframe_structure(df)
    return df


def create_genome_mappings(df_only_cutoffs, coords):
    # Create a mapping of gene names to their genomes
    gene_to_genome = dict(zip(coords['name'], coords['genome']))
    
    # Create the mappings using the gene_to_genome dictionary
    row_to_subsection = pd.Series(index=df_only_cutoffs.index, dtype="object")
    col_to_subsection = pd.Series(index=df_only_cutoffs.columns, dtype="object")

    # Map each row and column to its genome using the gene_to_genome dictionary
    for idx in df_only_cutoffs.index:
        row_to_subsection[idx] = gene_to_genome.get(idx)
    
    for col in df_only_cutoffs.columns:
        col_to_subsection[col] = gene_to_genome.get(col)

    return row_to_subsection, col_to_subsection

def calculate_column_maxes(df_only_cutoffs, row_to_subsection):
    col_max = pd.DataFrame(index=df_only_cutoffs.index, columns=df_only_cutoffs.columns)
    
    for col in df_only_cutoffs.columns:
        temp = pd.DataFrame({
            'value': df_only_cutoffs[col],
            'subsection': row_to_subsection
        })
        max_vals = temp.groupby('subsection')['value'].transform('max')
        col_max[col] = df_only_cutoffs[col].where(df_only_cutoffs[col] == max_vals)
    
    return col_max

def calculate_row_maxes(df_only_cutoffs, col_to_subsection):
    row_max = pd.DataFrame(index=df_only_cutoffs.index, columns=df_only_cutoffs.columns, dtype=float)
    
    for idx, row in df_only_cutoffs.iterrows():
        temp = pd.DataFrame({
            'value': row,
            'subsection': col_to_subsection
        })
        max_vals = temp.groupby('subsection')['value'].transform('max')
        row_max.loc[idx] = row.where(row == max_vals)
    
    return row_max

def parse_matrix_data(matrix_file, genomes, coord_df):
    try:
        print(matrix_file)
        # Read and prepare the dataframe
        df = prepare_dataframe(matrix_file)

        print("PRINTING DATAFRAME \n\n\n\n\n\n")
        print(df)

        # Validate matrix indices against coordinate names
        validate_matrix_coordinate_mapping(df, coord_df)
        
        # Get data above cutoff
        df_only_cutoffs = df[df >= 25]
        
        row_to_subsection, col_to_subsection = create_genome_mappings(df_only_cutoffs, coord_df)
        
        # Calculate maxes
        col_max = calculate_column_maxes(df_only_cutoffs, row_to_subsection)
        row_max = calculate_row_maxes(df_only_cutoffs, col_to_subsection)
        
        return {
            'df_only_cutoffs': df_only_cutoffs,
            'row_max': row_max,
            'col_max': col_max
        }
        
    except pd.errors.EmptyDataError:
        raise ValueError("The matrix file is empty or cannot be read")
    except pd.errors.ParserError:
        raise ValueError("Unable to parse the matrix file. Please ensure it's a valid Excel file")
    except Exception as e:
        raise ValueError(f"Error processing matrix file: {str(e)}")


def create_output(matrix_data, coords):
    output = {"genomes": coords['genome'].unique().tolist()}
    output["nodes"] = add_nodes(coords)
    output["links"] = add_links(matrix_data['df_only_cutoffs'], matrix_data['row_max'], matrix_data['col_max'], coords)
    return output

# Update the original parse_matrix function to use the new functions
def parse_matrix(matrix_file, coord_file):
    coords = parse_coordinates(coord_file)
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