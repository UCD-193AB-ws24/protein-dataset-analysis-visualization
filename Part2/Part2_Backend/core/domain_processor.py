from typing import List, Dict, Tuple
import pandas as pd
from core.domain_types import DomainColumn


class DomainProcessor:
    """
    Handles domain-related processing and validation operations.
    
    This class consolidates domain processing logic that was previously scattered
    across multiple files and functions.
    """
    
    def process_domain_field(self, df: pd.DataFrame) -> Tuple[List[str], List[str]]:
        """
        Process domain fields in a DataFrame and return domain names and column names.
        
        Args:
            df: DataFrame containing domain columns
            
        Returns:
            Tuple of (domain_names, domain_column_names)
            
        Raises:
            ValueError: If domain processing fails
        """
        try:
            # Extract domain columns
            domain_columns = self._extract_domain_columns(df)
            
            # Validate domain structure
            validation_errors = self._validate_domain_structure(domain_columns)
            if validation_errors:
                raise ValueError(f"Domain validation failed: {'; '.join(validation_errors)}")
            
            # Group domains and extract names
            domain_groups = self._group_domains(domain_columns)
            domain_names = list(domain_groups.keys())
            domain_col_names = [dc.name for dc in domain_columns]
            
            return domain_names, domain_col_names
            
        except Exception as e:
            raise ValueError(f"Error processing domain field: {str(e)}")
    
    def _extract_domain_columns(self, df: pd.DataFrame) -> List[DomainColumn]:
        """Extract and parse domain columns from a DataFrame."""
        domain_columns = []
        for col in df.columns:
            if 'domain' in col.lower():
                try:
                    domain_col = DomainColumn.from_column_name(col)
                    domain_columns.append(domain_col)
                except ValueError:
                    # Skip columns that don't follow the pattern
                    continue
        return domain_columns
    
    def _group_domains(self, domain_columns: List[DomainColumn]) -> Dict[str, List[DomainColumn]]:
        """Group domain columns by domain name."""
        domain_groups = {}
        for dc in domain_columns:
            if dc.domain_name not in domain_groups:
                domain_groups[dc.domain_name] = []
            domain_groups[dc.domain_name].append(dc)
        return domain_groups
    
    def _validate_domain_structure(self, domain_columns: List[DomainColumn]) -> List[str]:
        """Validate the structure of domain columns."""
        errors = []
        
        if not domain_columns:
            errors.append("No domain columns found (should be in format 'domainX_NAME_start/end/NA')")
            return errors
        
        # Group by domain name for validation
        domain_groups = self._group_domains(domain_columns)
        
        # Validate each domain group
        for domain_name, cols in domain_groups.items():
            has_start = any(col.column_type == 'start' for col in cols)
            has_end = any(col.column_type == 'end' for col in cols)
            
            # If domain has start/end positions, they must be in the same file
            if has_start or has_end:
                if not (has_start and has_end):
                    errors.append(f"Domain {domain_name} must have both start and end positions in the same file")
        
        return errors 