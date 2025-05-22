import pandas as pd
from io import BytesIO
from flask import jsonify
import json
import argparse
import sys
from file_utils import (
    read_file,
    validate_dataframe_basic, 
    validate_dataframe_structure,
    validate_coordinate_data_types
)


def validate_coordinate_dataframe_basic(df):
    if df.empty:
        raise ValueError("The coordinate file is empty")

    required_columns = ['name', 'protein_name', 'genome', 'gene_type', 'orientation']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

    if df['name'].isnull().any():
        raise ValueError("Found empty values in the name column")

    if df['position'].isnull().any():
        raise ValueError("Found empty values in the position column")

    if df['orientation'].isnull().any():
        raise ValueError("Found empty values in the orientation column")

def validate_coordinate_data_types(df):
    # Check if position is numeric or can be converted to numeric
    try:
        # First try direct numeric conversion
        if not pd.to_numeric(df['position'], errors='coerce').notnull().all():
            # If that fails, try converting strings to numeric
            df['position'] = df['position'].astype(str).str.strip()
            # Remove commas from numbers
            df['position'] = df['position'].str.replace(',', '')
            if not pd.to_numeric(df['position'], errors='coerce').notnull().all():
                raise ValueError("Position column contains values that cannot be converted to numbers")
    except Exception as e:
        raise ValueError(f"Error validating position values: {str(e)}")

    valid_orientations = {'minus', 'plus', 'negative', 'positive', '+', '-'}
    if not df['orientation'].isin(valid_orientations).all():
        raise ValueError("Orientation column should only contain 'plus', 'minus', 'positive', 'negative', '+' or '-'")

    # Convert each orientation individually
    df['orientation'] = df['orientation'].map({
        'positive': 'plus',
        '+': 'plus',
        'negative': 'minus',
        '-': 'minus'
    }).fillna(df['orientation'])  # Keep original value if not in mapping

def process_name_field(df):
    try:
        if df['protein_name'].isnull().any() or df['genome'].isnull().any():
            raise ValueError("Some names are empty")
        return df
    except Exception as e:
        raise ValueError(f"Error processing name field: {str(e)}")

def calculate_relative_positions(df):
    try:
        df['rel_position'] = df.groupby('genome')['position'].rank(method='first').astype(int)
        return df
    except Exception as e:
        raise ValueError(f"Error calculating relative positions: {str(e)}")

def process_domain_field(df):
    try:
        domain_columns = [col for col in df.columns if 'domain' in col]
        if len(domain_columns) == 0:
            raise ValueError("No domain columns found (should be in format 'domainX_NAME_start/end/NA)")

        domain_names = set()
        domain_col_names = set()
        for col in domain_columns:
            domain_col_names.add(col)
            parts = col.split('_')
            if len(parts) < 2:
                raise ValueError(f"Invalid domain format, needs underscore: {col}")

            if len(parts) == 3:
                domain_name = '_'.join(parts[1:-1]) # Also handles cases where domain names have underscores
            elif len(parts) == 2:
                domain_name = parts[-1]
            domain_names.add(domain_name)

        for domain in domain_names:
            test_domain_cols = [col for col in domain_columns if domain in col]
            has_start = any(col for col in test_domain_cols if col.endswith('_start'))
            has_end = any(col for col in test_domain_cols if col.endswith('_end')) 

            if (has_start or has_end) and not (has_start and has_end):
                raise ValueError(f"Domain {domain} is missing start or end position")

        return list(domain_names), list(domain_col_names)
    except Exception as e:
        raise ValueError(f"Error processing domain field: {str(e)}")

def calculate_relative_positions(df):
    try:
        df['rel_position'] = df.groupby('genome')['position'].rank(method='first').astype(int)
        return df
    except Exception as e:
        raise ValueError(f"Error calculating relative positions: {str(e)}")

def parse_coordinates(coord_file):
    try:
        df = read_file(coord_file, 'coordinate')

        # Validate basic structure
        validate_coordinate_dataframe_basic(df)

        # Validate data types
        validate_coordinate_data_types(df)

        domain_names, domain_col_names = process_domain_field(df)

        # Process name field
        df = process_name_field(df)

        # Calculate relative positions
        df = calculate_relative_positions(df)

        # Return only the required columns in the specified order
        required_columns = ['name', 'genome', 'protein_name', 'position', 'rel_position', 'orientation', 'gene_type']
        required_columns = required_columns + domain_col_names
        if not all(col in df.columns for col in required_columns):
            raise ValueError("Missing one or more required columns after processing")

        return df[required_columns]

    except pd.errors.EmptyDataError:
        raise ValueError("The coordinate file is empty or cannot be read")
    except Exception as e:
        if not isinstance(e, ValueError):  # Don't wrap ValueError as it's already formatted
            raise ValueError(f"Error processing coordinate file: {str(e)}")
        raise

def parse_filenames(file_names):
    domains = []
    for name in file_names:
        parts = name.split('domain') # ['2_NBS.xlsx']
        if len(parts) > 1:
            after_domain = parts[1]
            tokens = after_domain.split('_') # ['2','NBS.xlsx']
            if len(tokens) > 1:
                try:
                    domain_num = int(tokens[0])
                    domain_name = tokens[1].split('.')[0]
                    domains.append((domain_num, domain_name))
                except Exception as e:
                    raise ValueError(f"File name is in invalid format: {str(e)}")

    return [name for _, name in domains]



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

def extract_subsections(df_only_cutoffs):
    subsections = df_only_cutoffs.index.to_series().str.split("_").str[1]
    if subsections.isnull().any():
        raise ValueError("Some row names don't follow the expected format (should contain '_')")
    #print(subsections)
    return subsections.unique()

def create_subsection_mappings(df_only_cutoffs, subsections):
    row_to_subsection = pd.Series(index=df_only_cutoffs.index, dtype="object")
    col_to_subsection = pd.Series(index=df_only_cutoffs.columns, dtype="object")

    # Helper function to get subsection from full name
    def get_subsection(name):
        try:
            return name.split('_')[1]
        except IndexError:
            return None

    for section in subsections:
        # Map rows using the second token
        row_subsections = df_only_cutoffs.index.map(get_subsection)
        matching_rows = row_subsections == section
        if not matching_rows.any():
            raise ValueError(f"Subsection {section} has no matching rows")
        row_to_subsection.loc[matching_rows] = section

        # Map columns using the second token
        col_subsections = df_only_cutoffs.columns.map(get_subsection)
        matching_cols = col_subsections == section
        if not matching_cols.any():
            raise ValueError(f"Subsection {section} has no matching columns")
        col_to_subsection.loc[matching_cols] = section

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

def parse_matrix_data(matrix_file):
    try:
        # Read and prepare the dataframe
        df = prepare_dataframe(matrix_file)
        # print(df)

        # Get data above cutoff
        df_only_cutoffs = df_only_cutoffs = df[df > 55]

        # Extract subsections and create mappings
        subsections = extract_subsections(df_only_cutoffs)
        row_to_subsection, col_to_subsection = create_subsection_mappings(df_only_cutoffs, subsections)

        # Calculate maxes
        col_max = calculate_column_maxes(df_only_cutoffs, row_to_subsection)
        row_max = calculate_row_maxes(df_only_cutoffs, col_to_subsection)

        return {
            'df_only_cutoffs': df_only_cutoffs,
            'row_max': row_max,
            'col_max': col_max,
            'subsections': subsections
        }

    except pd.errors.EmptyDataError:
        raise ValueError("The matrix file is empty or cannot be read")
    except pd.errors.ParserError:
        raise ValueError("Unable to parse the matrix file. Please ensure it's a valid Excel file")
    except Exception as e:
        raise ValueError(f"Error processing matrix file: {str(e)}")


def add_nodes(coords, cutoff_index):
    nodes = []

    for i in range(len(coords)):
        present = coords['name'][i] in cutoff_index
        node_data = {
            "id": coords['name'][i],
            "genome_name": coords['genome'][i],
            "protein_name": coords['protein_name'][i],
            "direction": coords['orientation'][i],
            "rel_position": int(coords['rel_position'][i]),
            "gene_type": coords['gene_type'][i],
            "is_present": present
        }

        # Add domain coordinates if they exist
        domain_cols = [col for col in coords.columns if 'domain' in col]
        for col in domain_cols:
            if col.endswith('_start') or col.endswith('_end'):
                value = coords[col][i]
                # Convert NaN to None (which becomes null in JSON)
                node_data[col] = None if pd.isna(value) else value

        nodes.append(node_data)
    
    print(nodes)

    return nodes

def add_links(df_only_cutoffs, row_max, col_max, subsections, domain):
    links = []
    domain_connections = {}
    all_genes = {}
    all_genes[domain] = df_only_cutoffs.index.tolist()

    for row in df_only_cutoffs.index:
        for col in df_only_cutoffs.columns:
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

            domain_connections[f'{source}#{target}'] = {domain: reciprocal_max}


            if any((genome in source) and (genome in target) for genome in subsections):
                continue


            links.append({
                "source": source,
                "target": target,
                "score": float(df_only_cutoffs.at[row, col]),
                "is_reciprocal": reciprocal_max
            })

    return links, domain_connections, all_genes

def create_output(matrix_data, coords, domain):

    genomes = matrix_data['subsections'].tolist()
    nodes = add_nodes(coords, matrix_data['df_only_cutoffs'].index)
    links, domain_connections, domain_genes = add_links(matrix_data['df_only_cutoffs'], matrix_data['row_max'], matrix_data['col_max'], matrix_data['subsections'], domain)
    return genomes, nodes, links, domain_connections, domain_genes, matrix_data['df_only_cutoffs'].index

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
            if (all(dom_bool for u_key, _, dom_bool in unique_links if u_key == key or u_key == reverse_key) and
                all(not (source in all_domain_genes[i] and target in all_domain_genes[i])
                    for i, present in enumerate(present_in_domains) if not present)):
                link_type = "solid_color"
            # At least one reciprocal
            elif any(dom_bool for u_key, _, dom_bool in unique_links if u_key == key or u_key == reverse_key):
                link_type = "solid_red"
            else:
                link_type = "dotted_grey"
        else:
            if all(dom_bool for u_key, _, dom_bool in unique_links if u_key == key or u_key == reverse_key):
                link_type = "solid_color"
            else:
                link_type = "dotted_color"
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

# Update the original parse_matrix function to use the new functions
def domain_parse(matrix_files, coord_file, file_names):
    coords = parse_coordinates(coord_file)
    domains = parse_filenames(file_names)

    all_outputs = {}

    genomes_output = []
    all_domain_connections = []
    all_domain_genes = []
    total_genomes = set()
    total_gene_list = []

    for idx, matrix_file in enumerate(matrix_files, 1):
        graph_output = {"domain_name": domains[idx - 1]}
        matrix_file.seek(0)
        genomes, nodes, links, domain_connections, domain_genes, total_gene_list = create_output(parse_matrix_data(matrix_file), coords, domains[idx - 1])
        all_domain_connections.append(domain_connections)
        all_domain_genes.append(domain_genes)
        total_genomes.update(genomes)
        graph_output["genomes"] = genomes
        graph_output["nodes"] = nodes
        graph_output["links"] = links
        genomes_output.append(graph_output)

    
    #print(total_genomes)

    domain_graph_nodes = add_nodes(coords, total_gene_list)
    for node in domain_graph_nodes:
        node["is_present"] = True
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