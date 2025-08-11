import pandas as pd
from io import BytesIO
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsing.dataframe_utils import parse_comma_separated_number
from core.config import FileProcessingConfig
from core.coordinate_file import CoordinateFile

def test_parse_comma_separated_number():
    """Test the parse_comma_separated_number function."""
    print("Testing parse_comma_separated_number function...")
    
    # Test cases
    test_cases = [
        ("1,253,689", 1253689),
        ("1,253.689", 1253.689),
        ("1,000,000", 1000000),
        ("1,234,567.89", 1234567.89),
        ("1234567", 1234567),  # No commas
        ("1234.56", 1234.56),  # Decimal without commas
        ("", None),  # Empty string
        ("abc", None),  # Invalid
        ("1,2,3", 123),  # Multiple commas
    ]
    
    for input_val, expected in test_cases:
        result = parse_comma_separated_number(input_val)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{input_val}' -> {result} (expected: {expected})")

def test_coordinate_file_with_comma_numbers():
    """Test CoordinateFile with comma-separated numbers in position column."""
    print("\nTesting CoordinateFile with comma-separated numbers...")
    
    # Create test data with comma-separated numbers
    test_data = """name,protein_name,genome,gene_type,orientation,position
gene1,protein1,genome1,type1,plus,"1,253,689"
gene2,protein2,genome1,type2,minus,"2,500,000"
gene3,protein3,genome2,type1,plus,"3,750,123"
"""
    
    # Create file object
    file_obj = BytesIO(test_data.encode('utf-8'))
    
    # Create configuration
    config = FileProcessingConfig(parse_comma_separated_numbers=True)
    
    # Create CoordinateFile instance
    coord_file = CoordinateFile(file_obj, config, "test_coordinates.csv")
    
    # Load and validate data
    data = coord_file.load_data()
    is_valid = coord_file.validate()
    
    print(f"Data loaded: {len(data)} rows")
    print(f"Validation passed: {is_valid}")
    
    if not is_valid:
        print("Validation errors:")
        for error in coord_file.validation_errors:
            print(f"  - {error}")
    
    # Clean data
    cleaned_data = coord_file.clean()
    print(f"\nCleaned data position column:")
    print(cleaned_data['position'].tolist())
    
    # Check if positions are now numeric
    print(f"Position column dtype: {cleaned_data['position'].dtype}")
    print(f"All positions numeric: {pd.api.types.is_numeric_dtype(cleaned_data['position'])}")

if __name__ == "__main__":
    test_parse_comma_separated_number()
    test_coordinate_file_with_comma_numbers() 