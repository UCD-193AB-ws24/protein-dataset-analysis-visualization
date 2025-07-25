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

def read_file(file, file_type: str) -> pd.DataFrame:
    """Read a file into a pandas DataFrame based on its extension."""
    if hasattr(file, 'name'):
        filename = file.name.lower()
        validate_file_extension(filename, file_type)
    else:
        filename = 'temp.xlsx'
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(BytesIO(file.read()), encoding='utf-8')
        elif filename.endswith('.tsv'):
            df = pd.read_csv(BytesIO(file.read()), sep='\t', encoding='utf-8')
        else:
            df = pd.read_excel(BytesIO(file.read()), engine='openpyxl')
        return df
    except UnicodeDecodeError:
        raise ValueError("File encoding error. Please ensure the file is UTF-8 encoded.")
    except pd.errors.ParserError as e:
        if filename.endswith('.csv'):
            raise ValueError("CSV parsing error. Please ensure the file is properly formatted with comma separators.")
        elif filename.endswith('.tsv'):
            raise ValueError("TSV parsing error. Please ensure the file is properly formatted with tab separators.")
        else:
            raise ValueError(f"Excel parsing error: {str(e)}") 