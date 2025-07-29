from typing import Dict, Union, BinaryIO
from io import BytesIO
import pandas as pd
from core.base_file import DataFile
from core.config import FileProcessingConfig
from parsing.io_utils import read_file
from parsing.dataframe_utils import clean_dataframe_whitespace


class MatrixFile(DataFile):
    """Represents a matrix file with validation and processing."""
    
    def __init__(self, file_object: Union[BinaryIO, BytesIO], config: FileProcessingConfig, filename: str = None):
        super().__init__(file_object, 'matrix', config, filename)
        self.structure = config.matrix_structure
    
    def load_data(self) -> pd.DataFrame:
        """Load matrix data from file object."""
        
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
            cleaned_data = clean_dataframe_whitespace(cleaned_data)
        
        # Apply cutoff
        cleaned_data = self.structure.apply_cutoff(cleaned_data)
        
        return cleaned_data
    
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