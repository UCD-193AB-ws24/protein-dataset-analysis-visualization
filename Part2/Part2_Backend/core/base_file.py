from typing import List, Dict, Any, Union, BinaryIO, Optional
from io import BytesIO
import pandas as pd
from core.config import FileProcessingConfig


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