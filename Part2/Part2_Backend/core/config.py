from dataclasses import dataclass, field
from typing import Dict, List
from core.file_structures import CoordinateFileStructure, MatrixFileStructure

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
    # Validation mode settings
    validation_mode: str = "general"  # "general" or "domain"
    # Coordinate file specific settings
    coordinate_structure: CoordinateFileStructure = field(default_factory=CoordinateFileStructure)
    # Matrix file specific settings  
    matrix_structure: MatrixFileStructure = field(default_factory=MatrixFileStructure) 