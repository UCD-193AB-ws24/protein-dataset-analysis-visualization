from typing import List, Dict, Any, Union, BinaryIO
from io import BytesIO
import pandas as pd
from core.base_file import DataFile
from core.config import FileProcessingConfig
from core.enums import OrientationType
from core.domain_types import DomainColumn
from parsing.io_utils import read_file
from parsing.dataframe_utils import clean_dataframe_whitespace, parse_comma_separated_number
# Import here to avoid circular import
from parsing.domain_utils import process_domain_field


class CoordinateFile(DataFile):
    """Represents a coordinate file with validation and processing."""
    
    def __init__(self, file_object: Union[BinaryIO, BytesIO], config: FileProcessingConfig, filename: str = None):
        super().__init__(file_object, 'coordinate', config, filename)
        self.structure = config.coordinate_structure
        self.domain_columns: List[DomainColumn] = []
    
    def load_data(self) -> pd.DataFrame:
        """Load coordinate data from file object."""
        
        # Reset file pointer to beginning
        self.file_object.seek(0)
        self.data = read_file(self.file_object, 'coordinate')
        return self.data
    
    def validate(self) -> bool:
        """Validate coordinate file structure and data."""
        if self.data is None:
            self.validation_errors.append("No data loaded")
            return False
        
        # Basic structure validation
        structure_errors = self.structure.validate_column_structure(self.data, self.config.validation_mode)
        self.validation_errors.extend(structure_errors)
        
        # Domain column validation (only for domain mode)
        if self.config.validation_mode == "domain":
            self.domain_columns = self.structure.get_domain_columns(self.data)
            domain_errors = self.structure.validate_domain_columns(self.domain_columns)
            self.validation_errors.extend(domain_errors)
        
        # Data type validation
        for col, spec in self.structure.column_specifications.items():
            if col in self.data.columns:
                # Skip gene_type validation for general mode
                if col == 'gene_type' and self.config.validation_mode == "general":
                    continue
                col_errors = self._validate_column(col, spec)
                self.validation_errors.extend(col_errors)
        
        return len(self.validation_errors) == 0
    
    def _validate_column(self, column_name: str, specification: Dict[str, Any]) -> List[str]:
        """Validate a specific column against its specification."""
        errors = []
        column_data = self.data[column_name]
        
        # Check for empty values
        if not specification.get('allow_empty', True) and column_data.isnull().any():
            errors.append(f"Found empty values in {column_name} column")
        
        # Check data type
        if specification['type'] == 'numeric':
            # Special handling for position column with comma-separated numbers
            if column_name == 'position' and self.config.parse_comma_separated_numbers:
                # Try to parse comma-separated numbers first
                parsed_values = column_data.apply(parse_comma_separated_number)
                if parsed_values.notnull().all():
                    # Update the data with parsed values
                    self.data[column_name] = parsed_values
                    column_data = parsed_values
                else:
                    # Fall back to standard numeric validation
                    if not pd.to_numeric(column_data, errors='coerce').notnull().all():
                        errors.append(f"{column_name} column contains non-numeric values (including invalid comma-separated formats)")
            else:
                # Standard numeric validation for other columns
                if not pd.to_numeric(column_data, errors='coerce').notnull().all():
                    errors.append(f"{column_name} column contains non-numeric values")
        
        elif specification['type'] == 'categorical':
            valid_values = specification.get('valid_values', set())
            if not column_data.isin(valid_values).all():
                errors.append(f"{column_name} column contains invalid values")
        
        # Check length constraints
        max_length = specification.get('max_length')
        if max_length and column_data.astype(str).str.len().max() > max_length:
            errors.append(f"{column_name} column contains values longer than {max_length} characters")
        
        return errors
    
    def clean(self) -> pd.DataFrame:
        """Clean and normalize coordinate data."""
        if self.data is None:
            raise ValueError("No data to clean")
        
        cleaned_data = self.data.copy()
        
        # Clean comma-separated numbers in position column
        if self.config.parse_comma_separated_numbers and 'position' in cleaned_data.columns:
            cleaned_data = self._clean_comma_separated_numbers(cleaned_data, 'position')
        
        # Clean whitespace
        if self.config.clean_whitespace:
            cleaned_data = self._clean_whitespace(cleaned_data)
        
        # Normalize orientations
        if self.config.normalize_orientations and 'orientation' in cleaned_data.columns:
            cleaned_data['orientation'] = cleaned_data['orientation'].apply(OrientationType.normalize)
        
        # Handle missing values
        if self.config.handle_missing_values:
            cleaned_data = self._handle_missing_values(cleaned_data)
        
        # Calculate relative positions
        if 'position' in cleaned_data.columns and 'genome' in cleaned_data.columns:
            cleaned_data['rel_position'] = cleaned_data.groupby('genome')['position'].rank(method='first').astype(int)
        
        return cleaned_data
    
    def _clean_comma_separated_numbers(self, df: pd.DataFrame, column_name: str) -> pd.DataFrame:
        """Clean comma-separated numbers in a specific column."""
        if column_name not in df.columns:
            return df
        
        # Apply parsing function to the column
        parsed_values = df[column_name].apply(parse_comma_separated_number)
        
        # Update the column with parsed values where successful
        df[column_name] = parsed_values
        
        # Log warning for any values that couldn't be parsed
        failed_parses = df[column_name].isnull().sum()
        if failed_parses > 0:
            self.processing_warnings.append(
                f"Could not parse {failed_parses} values in {column_name} column as comma-separated numbers"
            )
        
        return df
    
    def _clean_whitespace(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean whitespace from DataFrame."""
        return clean_dataframe_whitespace(df)
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values with appropriate defaults."""
        # Fill missing gene_type with 'unknown'
        if 'gene_type' in df.columns:
            df['gene_type'] = df['gene_type'].fillna('unknown')
        
        return df

    def clean_with_domains(self) -> pd.DataFrame:
        """Clean and normalize coordinate data, including domain columns if present."""
        if self.data is None:
            raise ValueError("No data to clean")
        cleaned_data = self.clean()
        # Import here to avoid circular import
        domain_columns = [col for col in cleaned_data.columns if 'domain' in col]
        if domain_columns:
            domain_names, domain_col_names = process_domain_field(cleaned_data)
            required_columns = ['name', 'genome', 'protein_name', 'position', 'rel_position', 'orientation', 'gene_type'] + domain_col_names
            if not all(col in cleaned_data.columns for col in required_columns):
                raise ValueError("Missing one or more required columns after processing")
            return cleaned_data[required_columns]
        else:
            required_columns = ['name', 'genome', 'protein_name', 'position', 'rel_position', 'orientation']
            if not all(col in cleaned_data.columns for col in required_columns):
                raise ValueError("Missing one or more required columns after processing")
            return cleaned_data[required_columns] 