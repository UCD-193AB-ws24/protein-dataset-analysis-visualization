from dataclasses import dataclass

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