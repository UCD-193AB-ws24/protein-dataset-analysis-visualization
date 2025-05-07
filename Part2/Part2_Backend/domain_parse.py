import pandas as pd
from io import BytesIO
from flask import jsonify
import json


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
    # Check if position is numeric
    if not pd.to_numeric(df['position'], errors='coerce').notnull().all():
        raise ValueError("Position column contains non-numeric values")
        
    valid_orientations = {'minus', 'plus', 'negative', 'positive', '+', '-'}
    if not df['orientation'].isin(valid_orientations).all():
        raise ValueError("Orientation column should only contain 'plus', 'minus', 'positive', 'negative', '+' or '-'")

    if df['orientation'].isin(['positive', '+']).any():
        df['orientation'] = 'plus'
    elif df['orientation'].isin(['negative', '-']).any():
        df['orientation'] = 'minus'

def process_name_field(df):
    try:
        if df['protein_name'].isnull().any() or df['genome'].isnull().any():
            raise ValueError("Some names don't follow the expected format (should contain '_')")
            
        return df
    except Exception as e:
        raise ValueError(f"Error processing name field: {str(e)}")

def process_domain_field(df):
    try:
        domain_columns = [col for col in df.columns if 'domain' in col]
        if len(domain_columns) == 0:
            raise ValueError("No domain columns found (should be in format 'domainX_NAME_start/end)")
        
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
            has_end = (col for col in test_domain_cols if col.endswith('_end'))

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
        # Read the Excel file
        df = pd.read_excel(BytesIO(coord_file.read()), engine='openpyxl')
        
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
        print(required_columns)
        if not all(col in df.columns for col in required_columns):
            raise ValueError("Missing one or more required columns after processing")
        
        print(df[required_columns])
            
        return df[required_columns]
        
    except pd.errors.EmptyDataError:
        raise ValueError("The coordinate file is empty or cannot be read")
    except pd.errors.ParserError:
        raise ValueError("Unable to parse the coordinate file. Please ensure it's a valid Excel file")
    except Exception as e:
        raise ValueError(f"Error processing coordinate file: {str(e)}")

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
                
    domains.sort(key = lambda x: x[0])

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
    df = pd.read_excel(BytesIO(matrix_file.read()), engine='openpyxl')
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
    print(subsections)
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
        print(df)
        
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
        nodes.append({
            "id" : coords['name'][i],
            "genome_name": coords['genome'][i],
            "protein_name": coords['protein_name'][i],
            "direction": coords['orientation'][i],
            "rel_position": int(coords['rel_position'][i]),
            "gene_type": coords['gene_type'][i],
            "is_present": present
            # Extra flag "inconsistent": T/F
        })

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

# def get_gene_names_by_genome(coords):
#     gene_names_by_genome = {}
#     all_names = coords['name'].tolist()
#     for genome in coords['genome']:
#         gene_names_by_genome[genome] = [name for name in all_names if genome in name]
#     return gene_names_by_genome

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
    print(all_keys)
    print(unique_links)
    for domain_dict in all_domain_connections:
        for key, value in domain_dict.items():
            all_keys.add(key)
            for item in value:
                if isinstance(item, str):
                    unique_links.add((key, item)) # ("source_target", "TIR")

    combined = []
    num_domains = len(domains)

    for key in all_keys:
        source, target = key.split('#', 1)
        reverse_key = f"{target}#{source}"
        # Check if this key exists in all domain dicts

        # Create list of tuples containing (key, domain) for each domain
        key_domain_pairs = [(key, domain) for domain in domains]
        reverse_key_pairs = [(reverse_key, domain) for domain in domains]
        present_in_domains = [
            all((pair in unique_links or (reverse_key_pairs[i] in unique_links)) for i, pair in enumerate(key_domain_pairs))
        ]

        link_type = ""

        if not all(present_in_domains):
            # Gene doesn't exist in one domain
            if not all(source in all_domain_genes[i] and target in all_domain_genes[i] 
                       for i, present in enumerate(present_in_domains) if not present):
                link_type = "solid_color"
            # At least one reciprocal
            elif any(any(domain_dict.get(key, {}).get(domain, False) or domain_dict.get(reverse_key, {}).get(domain, False)
                        for domain in domains)
                        for domain_dict in all_domain_connections):
                link_type = "solid_red"
            else:
                link_type = "dotted_grey"
        else:
            # Check if any domain type is consistent across all connections
            if any(all(key in domain_dict and domain_dict[key].get(domain, False) 
                       for domain_dict in all_domain_connections) 
                       for domain in domains):
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
    print(combined)

    return combined

# Update the original parse_matrix function to use the new functions
def domain_parse(matrix_files, coord_file, file_names):
    coords = parse_coordinates(coord_file)
    domains = parse_filenames(file_names)

    all_outputs = {}

    genomes_output = []
    # gene_names_by_genome = get_gene_names_by_genome(coords)
    #
    # all_outputs['genes_by_genomes'] = gene_names_by_genome
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

    domain_graph_nodes = add_nodes(coords, total_gene_list)
    domain_graph = {
        "domain_name": "ALL",
        "genomes": list(total_genomes),
        "nodes": domain_graph_nodes,
        "links": combine_graphs(all_domain_connections, all_domain_genes, domains)
    }

    genomes_output.append(domain_graph)

    return genomes_output


if __name__ == "__main__":
    import argparse
    import sys
    
    # Create argument parser
    parser = argparse.ArgumentParser(description='Parse matrix and coordinate files for genome visualization')
    parser.add_argument('matrix_file_1', type=str, help='Path to the first matrix Excel file')
    parser.add_argument('matrix_file_2', type=str, help='Path to the second matrix Excel file')
    parser.add_argument('matrix_file_3', type=str, help='Path to the third matrix Excel file')
    parser.add_argument('coord_file', type=str, help='Path to the coordinate Excel file')
    parser.add_argument('--output', '-o', type=str, help='Output JSON file path (optional, defaults to stdout)')
    
    # Parse arguments
    args = parser.parse_args()
    
    try:
        with open(args.matrix_file_1, 'rb') as matrix_file_1, \
             open(args.matrix_file_2, 'rb') as matrix_file_2, \
             open(args.matrix_file_3, 'rb') as matrix_file_3, \
             open(args.coord_file, 'rb') as coord_file:

            matrix_files = [matrix_file_1, matrix_file_2, matrix_file_3]
            file_names = [matrix_file_1.name, matrix_file_2.name, matrix_file_3.name]
            result_obj = domain_parse(matrix_files, coord_file, file_names)

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