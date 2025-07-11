from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Any, Union, BinaryIO
from enum import Enum
import pandas as pd
import numpy as np
from io import BytesIO
import re


class OrientationType(Enum):
    """Valid orientation values for coordinate files."""
    PLUS = "plus"
    MINUS = "minus"
    
    @classmethod
    def get_valid_inputs(cls) -> Set[str]:
        """Get all valid input strings that map to orientation values."""
        return {'plus', 'minus', 'positive', 'negative', '+', '-'}
    
    @classmethod
    def normalize(cls, value: str) -> str:
        """Normalize orientation value to standard format."""
        mapping = {
            'positive': 'plus',
            '+': 'plus', 
            'negative': 'minus',
            '-': 'minus'
        }
        return mapping.get(value.lower().strip(), value.lower().strip())


@dataclass
class DomainColumn:
    """Represents a domain column in coordinate files."""
    name: str
    domain_name: str
    column_type: str  # 'start', 'end', or 'NA'
    
    @classmethod
    def from_column_name(cls, column_name: str) -> 'DomainColumn':
        """Create DomainColumn from column name like 'domain1_TIR_start'."""
        parts = column_name.split('_')
        if len(parts) < 2:
            raise ValueError(f"Invalid domain column format: {column_name}")
        
        if len(parts) == 2:
            # Format: domain1_NAME
            domain_name = parts[1]
            column_type = 'NA'
        elif len(parts) >= 3:
            # Format: domain1_NAME_start or domain1_NAME_end
            domain_name = '_'.join(parts[1:-1])  # Handle domain names with underscores
            column_type = parts[-1]
        else:
            raise ValueError(f"Invalid domain column format: {column_name}")
        
        return cls(
            name=column_name,
            domain_name=domain_name,
            column_type=column_type
        )


@dataclass
class CoordinateFileStructure:
    """Defines the expected structure of coordinate files."""
    
    # Required columns that must be present
    required_columns: List[str] = field(default_factory=lambda: [
        'name', 'protein_name', 'genome', 'gene_type', 'orientation', 'position'
    ])
    
    # Column data types and validation rules
    column_specifications: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        'name': {
            'type': 'string',
            'required': True,
            'max_length': 100,
            'allow_empty': False
        },
        'protein_name': {
            'type': 'string', 
            'required': True,
            'max_length': 100,
            'allow_empty': False
        },
        'genome': {
            'type': 'string',
            'required': True,
            'max_length': 100,
            'allow_empty': False
        },
        'gene_type': {
            'type': 'string',
            'required': True,
            'max_length': 50,
            'allow_empty': False
        },
        'position': {
            'type': 'numeric',
            'required': True,
            'allow_empty': False,
            'min_value': 0
        },
        'orientation': {
            'type': 'categorical',
            'required': True,
            'allow_empty': False,
            'valid_values': OrientationType.get_valid_inputs()
        }
    })
    
    # Domain column patterns
    domain_column_pattern: str = "domain*_*_*"  # domain1_NAME_start/end/NA
    
    # Computed columns that will be added during processing
    computed_columns: List[str] = field(default_factory=lambda: ['rel_position'])
    
    def get_all_required_columns(self) -> List[str]:
        """Get all required columns including computed ones."""
        return self.required_columns + self.computed_columns
    
    def validate_column_structure(self, df: pd.DataFrame) -> List[str]:
        """Validate that DataFrame has required column structure."""
        errors = []
        
        # Check required columns
        missing_columns = set(self.required_columns) - set(df.columns)
        if missing_columns:
            errors.append(f"Missing required columns: {', '.join(missing_columns)}")
        
        return errors
    
    def get_domain_columns(self, df: pd.DataFrame) -> List[DomainColumn]:
        """Extract domain columns from DataFrame."""
        domain_columns = []
        for col in df.columns:
            if 'domain' in col.lower():
                try:
                    domain_col = DomainColumn.from_column_name(col)
                    domain_columns.append(domain_col)
                except ValueError as e:
                    # Log warning but don't fail - some columns might not follow pattern
                    continue
        return domain_columns
    
    def validate_domain_columns(self, domain_columns: List[DomainColumn]) -> List[str]:
        """Validate domain column structure."""
        errors = []
        
        if not domain_columns:
            errors.append("No domain columns found (should be in format 'domainX_NAME_start/end/NA')")
            return errors
        
        # Group by domain name
        domain_groups = {}
        for col in domain_columns:
            if col.domain_name not in domain_groups:
                domain_groups[col.domain_name] = []
            domain_groups[col.domain_name].append(col)
        
        # Validate each domain group
        for domain_name, cols in domain_groups.items():
            has_start = any(col.column_type == 'start' for col in cols)
            has_end = any(col.column_type == 'end' for col in cols)
            
            # If domain has start/end positions, they must be in the same file
            if has_start or has_end:
                if not (has_start and has_end):
                    errors.append(f"Domain {domain_name} must have both start and end positions in the same file")
        
        return errors


@dataclass
class MatrixFileStructure:
    """Defines the expected structure of matrix files."""
    
    # Minimum size requirements
    min_rows: int = 2
    min_columns: int = 2
    
    # Data type requirements
    required_data_type: str = "numeric"
    
    # Validation rules
    validation_rules: Dict[str, Any] = field(default_factory=lambda: {
        'allow_duplicate_indices': False,
        'allow_duplicate_columns': False,
        'allow_empty_rows': False,
        'allow_empty_columns': False,
        'max_index_length': 100,
        'max_column_length': 100,
        'allow_negative_values': True,
        'allow_zero_values': True
    })
    
    # Processing parameters
    cutoff_threshold: float = 25.0
    
    def validate_structure(self, df: pd.DataFrame) -> List[str]:
        """Validate matrix DataFrame structure."""
        errors = []
        
        # Check minimum size
        if len(df) < self.min_rows:
            errors.append(f"Matrix must have at least {self.min_rows} rows")
        
        if len(df.columns) < self.min_columns:
            errors.append(f"Matrix must have at least {self.min_columns} columns")
        
        # Check for duplicates
        if not self.validation_rules['allow_duplicate_indices'] and df.index.duplicated().any():
            errors.append("Matrix contains duplicate row identifiers")
        
        if not self.validation_rules['allow_duplicate_columns'] and df.columns.duplicated().any():
            errors.append("Matrix contains duplicate column names")
        
        # Check for empty rows/columns
        if not self.validation_rules['allow_empty_rows'] and df.dropna(how='all').empty:
            errors.append("Matrix is empty after removing NA values")
        
        if not self.validation_rules['allow_empty_columns'] and df.dropna(axis=1, how='all').empty:
            errors.append("Matrix has no valid columns after removing NA values")
        
        # Check data types
        if not df.dtypes.apply(lambda x: pd.api.types.is_numeric_dtype(x)).all():
            errors.append("Matrix contains non-numeric values")
        
        # Check index and column lengths
        if any(len(str(idx)) > self.validation_rules['max_index_length'] for idx in df.index):
            errors.append(f"Matrix contains row identifiers longer than {self.validation_rules['max_index_length']} characters")
        
        if any(len(str(col)) > self.validation_rules['max_column_length'] for col in df.columns):
            errors.append(f"Matrix contains column names longer than {self.validation_rules['max_column_length']} characters")
        
        return errors
    
    def apply_cutoff(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply cutoff threshold to matrix data."""
        return df[df >= self.cutoff_threshold]


@dataclass
class FileProcessingConfig:
    """Configuration for file processing operations."""
    
    # File reading settings
    supported_formats: Dict[str, List[str]] = field(default_factory=lambda: {
        'matrix': ['.xlsx', '.csv', '.tsv'],
        'coordinate': ['.xlsx', '.csv', '.tsv']
    })
    
    # Data cleaning settings
    clean_whitespace: bool = True
    normalize_orientations: bool = True
    handle_missing_values: bool = True
    parse_comma_separated_numbers: bool = True  # New option for comma-separated number parsing
    
    # Error handling settings
    strict_validation: bool = True
    allow_partial_processing: bool = False
    
    # Coordinate file specific settings
    coordinate_structure: CoordinateFileStructure = field(default_factory=CoordinateFileStructure)
    
    # Matrix file specific settings  
    matrix_structure: MatrixFileStructure = field(default_factory=MatrixFileStructure)


class DataFile:
    """Base class for data files with common functionality."""
    
    def __init__(self, file_object: Union[BinaryIO, BytesIO], file_type: str, config: FileProcessingConfig, filename: str = None):
        self.file_object = file_object
        self.file_type = file_type
        self.config = config
        self.filename = filename or getattr(file_object, 'name', 'unknown')
        self.data: Optional[pd.DataFrame] = None
        self.validation_errors: List[str] = []
        self.processing_warnings: List[str] = []
    
    def load_data(self) -> pd.DataFrame:
        """Load data from file object."""
        raise NotImplementedError
    
    def validate(self) -> bool:
        """Validate data structure."""
        raise NotImplementedError
    
    def clean(self) -> pd.DataFrame:
        """Clean and normalize data."""
        raise NotImplementedError
    
    def get_validation_report(self) -> Dict[str, Any]:
        """Get detailed validation report."""
        return {
            'is_valid': len(self.validation_errors) == 0,
            'errors': self.validation_errors,
            'warnings': self.processing_warnings,
            'file_type': self.file_type,
            'filename': self.filename
        }


class CoordinateFile(DataFile):
    """Represents a coordinate file with validation and processing."""
    
    def __init__(self, file_object: Union[BinaryIO, BytesIO], config: FileProcessingConfig, filename: str = None):
        super().__init__(file_object, 'coordinate', config, filename)
        self.structure = config.coordinate_structure
        self.domain_columns: List[DomainColumn] = []
    
    def load_data(self) -> pd.DataFrame:
        """Load coordinate data from file object."""
        from file_utils import read_file
        
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
        structure_errors = self.structure.validate_column_structure(self.data)
        self.validation_errors.extend(structure_errors)
        
        # Domain column validation
        self.domain_columns = self.structure.get_domain_columns(self.data)
        domain_errors = self.structure.validate_domain_columns(self.domain_columns)
        self.validation_errors.extend(domain_errors)
        
        # Data type validation
        for col, spec in self.structure.column_specifications.items():
            if col in self.data.columns:
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
        from file_utils import clean_dataframe_whitespace
        return clean_dataframe_whitespace(df)
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values with appropriate defaults."""
        # Fill missing gene_type with 'unknown'
        if 'gene_type' in df.columns:
            df['gene_type'] = df['gene_type'].fillna('unknown')
        
        return df


class MatrixFile(DataFile):
    """Represents a matrix file with validation and processing."""
    
    def __init__(self, file_object: Union[BinaryIO, BytesIO], config: FileProcessingConfig, filename: str = None):
        super().__init__(file_object, 'matrix', config, filename)
        self.structure = config.matrix_structure
    
    def load_data(self) -> pd.DataFrame:
        """Load matrix data from file object."""
        from file_utils import read_file
        
        # Reset file pointer to beginning
        self.file_object.seek(0)
        raw_data = read_file(self.file_object, 'matrix')
        
        # Prepare matrix structure
        self.data = raw_data.reset_index(drop=True)
        self.data = self.data.set_index(self.data.columns[0])
        self.data.index.name = None
        
        # Remove empty rows and columns
        self.data = self.data.dropna(how='all')
        self.data = self.data.dropna(axis=1, how='all')
        
        return self.data
    
    def validate(self) -> bool:
        """Validate matrix file structure and data."""
        if self.data is None:
            self.validation_errors.append("No data loaded")
            return False
        
        # Structure validation
        structure_errors = self.structure.validate_structure(self.data)
        self.validation_errors.extend(structure_errors)
        
        return len(self.validation_errors) == 0
    
    def clean(self) -> pd.DataFrame:
        """Clean and normalize matrix data."""
        if self.data is None:
            raise ValueError("No data to clean")
        
        cleaned_data = self.data.copy()
        
        # Clean whitespace
        if self.config.clean_whitespace:
            cleaned_data = self._clean_whitespace(cleaned_data)
        
        # Apply cutoff
        cleaned_data = self.structure.apply_cutoff(cleaned_data)
        
        return cleaned_data
    
    def _clean_whitespace(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean whitespace from DataFrame."""
        from file_utils import clean_dataframe_whitespace
        return clean_dataframe_whitespace(df)
    
    def get_processed_data(self) -> Dict[str, pd.DataFrame]:
        """Get processed matrix data with max calculations."""
        if self.data is None:
            raise ValueError("No data loaded")
        
        # Apply cutoff
        df_cutoff = self.structure.apply_cutoff(self.data)
        
        return {
            'df_only_cutoffs': df_cutoff,
            'original_data': self.data
        }


def parse_comma_separated_number(value: str) -> Union[int, float, None]:
    """
    Parse a string that may contain comma-separated numbers.
    
    Args:
        value: String that may be in format "1,253,689" or "1,253.689"
    
    Returns:
        Parsed number or None if parsing fails
    """
    if pd.isna(value) or value == '':
        return None
    
    # Convert to string if it's not already
    value_str = str(value).strip()
    
    # Remove commas and try to parse
    try:
        # Remove all commas and parse
        cleaned_value = value_str.replace(',', '')
        return float(cleaned_value) if '.' in cleaned_value else int(cleaned_value)
    except (ValueError, TypeError):
        return None
