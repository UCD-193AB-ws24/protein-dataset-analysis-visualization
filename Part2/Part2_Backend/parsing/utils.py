from typing import Union
import pandas as pd

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