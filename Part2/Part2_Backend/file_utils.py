import pandas as pd
from io import BytesIO
from data_structures import CoordinateFile, MatrixFile, FileProcessingConfig

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


def validate_file_extension(filename: str, file_type: str) -> None:
    valid_extensions = {
        'matrix': ['.xlsx', '.csv', '.tsv'],
        'coordinate': ['.xlsx', '.csv', '.tsv']
    }
    
    if not any(filename.lower().endswith(ext) for ext in valid_extensions[file_type]):
        raise ValueError(
            f"Invalid {file_type} file format. Supported formats are: " + 
            ", ".join(ext.upper() for ext in valid_extensions[file_type])
        )

def clean_dataframe_whitespace(df: pd.DataFrame) -> pd.DataFrame:
    """Clean whitespace from DataFrame index, columns, and string values."""
    # Clean index and column names
    if df.index.dtype == "object":
        df.index = df.index.str.strip()
    df.columns = df.columns.str.strip()
    # Clean string values in all columns
    for col in df.columns:
        if df[col].dtype == "object":
            # Convert to string first, then strip
            df[col] = df[col].astype(str).str.strip()
            # Convert back to original type if possible
            try:
                if df[col].str.isnumeric().all():
                    df[col] = pd.to_numeric(df[col])
            except:
                pass  # Keep as string if conversion fails
    
    return df

def read_file(file, file_type: str) -> pd.DataFrame:
    """Read a file into a pandas DataFrame based on its extension."""
    # Handle both file objects and BytesIO objects
    if hasattr(file, 'name'):
        filename = file.name.lower()
        validate_file_extension(filename, file_type)
    else:
        # For BytesIO objects, we need to determine the file type from the content
        # For now, we'll assume it's an Excel file since that's the most common case
        filename = 'temp.xlsx'
    
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(BytesIO(file.read()), encoding='utf-8')
        elif filename.endswith('.tsv'):
            df = pd.read_csv(BytesIO(file.read()), sep='\t', encoding='utf-8')
        else:  # Excel file
            df = pd.read_excel(BytesIO(file.read()), engine='openpyxl')
            
        # Clean whitespace from the DataFrame
        df = clean_dataframe_whitespace(df)
            
    except UnicodeDecodeError:
        raise ValueError("File encoding error. Please ensure the file is UTF-8 encoded.")
    except pd.errors.ParserError as e:
        if filename.endswith('.csv'):
            raise ValueError("CSV parsing error. Please ensure the file is properly formatted with comma separators.")
        elif filename.endswith('.tsv'):
            raise ValueError("TSV parsing error. Please ensure the file is properly formatted with tab separators.")
        else:
            raise ValueError(f"Excel parsing error: {str(e)}")
    
    return df

def validate_dataframe_basic(df: pd.DataFrame) -> None:
    """Validate basic DataFrame structure."""
    if df.empty:
        raise ValueError("The file is empty")
    if len(df.columns) < 2 or len(df.index) < 2:
        raise ValueError("Matrix must have at least 2 rows and 2 columns")
    if len(df.columns) == 0:
        raise ValueError("Matrix must have at least one column for index")

def validate_dataframe_structure(df: pd.DataFrame) -> None:
    """Validate DataFrame structure and data types."""
    if df.index.duplicated().any():
        raise ValueError("Matrix contains duplicate row identifiers")
    if df.columns.duplicated().any():
        raise ValueError("Matrix contains duplicate column names")
    if df.empty:
        raise ValueError("Matrix is empty after removing NA values")
    if not df.dtypes.apply(lambda x: pd.api.types.is_numeric_dtype(x)).all():
        raise ValueError("Matrix contains non-numeric values") 
    
    # Check index and column lengths
    if any(len(str(idx)) > 100 for idx in df.index):
        raise ValueError("Matrix contains row identifiers longer than 100 characters")
    if any(len(str(col)) > 100 for col in df.columns):
        raise ValueError("Matrix contains column names longer than 100 characters")
    
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


def validate_coordinate_data_types(df):
    # Clean column names by stripping whitespace
    df.columns = df.columns.str.strip()
    
    # # Check name column length
    # if 'name' in df.columns and any(len(str(name)) > 100 for name in df['name']):
    #     raise ValueError("Coordinate file contains names longer than 100 characters")
    
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

    # Strip whitespace from orientation values
    df['orientation'] = df['orientation'].astype(str).str.strip()

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

def validate_matrix_coordinate_mapping(matrix_df: pd.DataFrame, coord_df: pd.DataFrame) -> None:
    """Validate that all matrix indices exist in the coordinate file's name column."""
    matrix_indices = set(matrix_df.index)
    coord_names = set(coord_df['name'])
    
    missing_names = matrix_indices - coord_names
    if missing_names:
        raise ValueError(
            f"Matrix contains {len(missing_names)} identifiers not found in coordinate file: " + 
            ", ".join(sorted(missing_names))
        )
    
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

def parse_coordinates(coord_file, include_domains=False):
    """
    Parse coordinate file using the new data structures.
    
    Args:
        coord_file: File object to parse
        include_domains: Whether to include domain columns in the output
    
    Returns:
        pd.DataFrame: Processed coordinate data
    """
    try:
        # Create configuration
        config = FileProcessingConfig()
        
        # Create coordinate file object
        coord_file_obj = CoordinateFile(coord_file, config)
        
        # Load and validate data
        coord_file_obj.load_data()
        
        if not coord_file_obj.validate():
            validation_report = coord_file_obj.get_validation_report()
            raise ValueError(f"Coordinate file validation failed: {validation_report['errors']}")
        
        # Clean data
        cleaned_data = coord_file_obj.clean()
        
        if include_domains:
            # Process domain fields (this is specific to domain parsing)
            from domain_parse import process_domain_field
            domain_names, domain_col_names = process_domain_field(cleaned_data)
            
            # Return only the required columns in the specified order
            required_columns = ['name', 'genome', 'protein_name', 'position', 'rel_position', 'orientation', 'gene_type']
            required_columns = required_columns + domain_col_names
        else:
            # Return only the required columns for matrix parsing (no domain columns)
            required_columns = ['name', 'genome', 'protein_name', 'position', 'rel_position', 'orientation']
        
        if not all(col in cleaned_data.columns for col in required_columns):
            raise ValueError("Missing one or more required columns after processing")
            
        return cleaned_data[required_columns]
        
    except pd.errors.EmptyDataError:
        raise ValueError("The coordinate file is empty or cannot be read")
    except Exception as e:
        if not isinstance(e, ValueError):  # Don't wrap ValueError as it's already formatted
            raise ValueError(f"Error processing coordinate file: {str(e)}")
        raise

def parse_matrix_data(matrix_file, genomes, coord_df):
    """
    Parse matrix data using the new data structures.
    
    Args:
        matrix_file: File object to parse
        genomes: List of genome names
        coord_df: Coordinate DataFrame for validation
    
    Returns:
        dict: Dictionary containing processed matrix data
    """
    try:
        # Create configuration
        config = FileProcessingConfig()
        
        # Create matrix file object
        matrix_file_obj = MatrixFile(matrix_file, config)
        
        # Load and validate data
        matrix_file_obj.load_data()
        
        if not matrix_file_obj.validate():
            validation_report = matrix_file_obj.get_validation_report()
            raise ValueError(f"Matrix file validation failed: {validation_report['errors']}")
        
        # Clean data (this applies cutoff)
        cleaned_data = matrix_file_obj.clean()
        
        # Validate matrix indices against coordinate names
        validate_matrix_coordinate_mapping(cleaned_data, coord_df)

        # Get data above cutoff (already done in clean(), but get it explicitly)
        df_only_cutoffs = cleaned_data

        # Create genome mappings and calculate maxes
        row_to_subsection, col_to_subsection = create_genome_mappings(df_only_cutoffs, coord_df)
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