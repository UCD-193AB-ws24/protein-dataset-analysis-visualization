from dataclasses import dataclass, field
from typing import List, Dict, Set, Any
import pandas as pd
from core.enums import OrientationType
from core.domain_types import DomainColumn


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
    
    def validate_column_structure(self, df: pd.DataFrame, validation_mode: str = "general") -> List[str]:
        """Validate that DataFrame has required column structure."""
        errors = []
        
        # Check required columns
        required_cols_for_validation = self.required_columns.copy()
        if validation_mode == "general":
            required_cols_for_validation.remove('gene_type')
        
        missing_columns = set(required_cols_for_validation) - set(df.columns)
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