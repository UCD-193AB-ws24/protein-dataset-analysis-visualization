import pandas as pd
from core.coordinate_file import CoordinateFile
from core.matrix_file import MatrixFile
from core.config import FileProcessingConfig
from parsing.domain_utils import process_domain_field


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