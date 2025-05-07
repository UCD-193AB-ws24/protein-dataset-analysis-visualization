import pandas as pd
from io import BytesIO
from flask import jsonify


def validate_coordinate_dataframe_basic(df):
    if df.empty:
        raise ValueError("The coordinate file is empty")
        
    required_columns = ['name', 'position', 'orientation']
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
        
    valid_orientations = {'minus', 'plus'}
    if not df['orientation'].isin(valid_orientations).all():
        raise ValueError("Orientation column should only contain plus or minus")

def process_name_field(df):
    try:
        # Remove Lsativa_ prefix if it exists
        df['name'] = df['name'].str.replace('^Lsativa_', '', regex=True)
        
        df['protein_name'] = df['name'].str.split('_').str[-1]
        df['genome_name'] = df['name'].str.split('_').str[0]
        
        if df['protein_name'].isnull().any() or df['genome_name'].isnull().any():
            raise ValueError("Some names don't follow the expected format (should contain '_')")
            
        return df
    except Exception as e:
        raise ValueError(f"Error processing name field: {str(e)}")

def calculate_relative_positions(df):
    try:
        df['rel_position'] = df.groupby('genome_name')['position'].rank(method='first').astype(int)
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
        
        # Process name field
        df = process_name_field(df)
        
        # Calculate relative positions
        df = calculate_relative_positions(df)
        
        # Return only the required columns in the specified order
        required_columns = ['name', 'genome_name', 'protein_name', 'position', 'rel_position', 'orientation']
        if not all(col in df.columns for col in required_columns):
            raise ValueError("Missing one or more required columns after processing")
            
        return df[required_columns]
        
    except pd.errors.EmptyDataError:
        raise ValueError("The coordinate file is empty or cannot be read")
    except pd.errors.ParserError:
        raise ValueError("Unable to parse the coordinate file. Please ensure it's a valid Excel file")
    except Exception as e:
        raise ValueError(f"Error processing coordinate file: {str(e)}")


def add_nodes(coords):
    nodes = []

    for i in range(len(coords)):
        nodes.append({
            "id" : '_'.join([coords['genome_name'][i], coords['protein_name'][i]]),
            "genome_name": coords['genome_name'][i],
            "protein_name": coords['protein_name'][i],
            "direction": coords['orientation'][i],
            "rel_position": int(coords['rel_position'][i]),
        })

    return nodes

def add_links(df_only_cutoffs, row_max, col_max, subsections):
    links = []

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

            if any((genome in source) and (genome in target) for genome in subsections):
                continue


            links.append({
                "source": source,
                "target": target,
                "score": float(df_only_cutoffs.at[row, col]),
                "is_reciprocal": reciprocal_max
            })

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
    subsections = df_only_cutoffs.index.to_series().str.split("_").str[0]
    if subsections.isnull().any():
        raise ValueError("Some row names don't follow the expected format (should contain '_')")
    return subsections.unique()

def create_subsection_mappings(df_only_cutoffs, subsections):
    row_to_subsection = pd.Series(index=df_only_cutoffs.index, dtype="object")
    col_to_subsection = pd.Series(index=df_only_cutoffs.columns, dtype="object")
    
    for section in subsections:
        # Map rows
        matching_rows = df_only_cutoffs.index.str.startswith(section)
        if not matching_rows.any():
            raise ValueError(f"Subsection {section} has no matching rows")
        row_to_subsection.loc[matching_rows] = section
        
        # Map columns
        matching_cols = df_only_cutoffs.columns.str.startswith(section)
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


def create_output(matrix_data, coords):
    output = {"genomes": matrix_data['subsections'].tolist()}
    output["nodes"] = add_nodes(coords)
    output["links"] = add_links(matrix_data['df_only_cutoffs'], matrix_data['row_max'], matrix_data['col_max'], matrix_data['subsections'])
    return output

# Update the original parse_matrix function to use the new functions
def parse_matrix(matrix_file, coord_file):
    matrix_data = parse_matrix_data(matrix_file)
    coords = parse_coordinates(coord_file)
    return create_output(matrix_data, coords)