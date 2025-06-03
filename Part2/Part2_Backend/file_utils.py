import pandas as pd
from io import BytesIO

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
        raise ValueError("Data must have at least 2 rows and 2 columns")
    if len(df.columns) == 0:
        raise ValueError("File must have at least one column for index")

def validate_dataframe_structure(df: pd.DataFrame) -> None:
    """Validate DataFrame structure and data types."""
    if df.index.duplicated().any():
        raise ValueError("Data contains duplicate row identifiers")
    if df.columns.duplicated().any():
        raise ValueError("Data contains duplicate column names")
    if df.empty:
        raise ValueError("Data is empty after removing NA values")
    if not df.dtypes.apply(lambda x: pd.api.types.is_numeric_dtype(x)).all():
        raise ValueError("Data contains non-numeric values") 
    
    # Check index and column lengths
    if any(len(str(idx)) > 100 for idx in df.index):
        raise ValueError("Matrix contains row identifiers longer than 100 characters")
    if any(len(str(col)) > 100 for col in df.columns):
        raise ValueError("Matrix contains column names longer than 100 characters")
    
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