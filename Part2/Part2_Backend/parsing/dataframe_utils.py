import pandas as pd
from typing import Union

def clean_dataframe_whitespace(df: pd.DataFrame) -> pd.DataFrame:
    """Clean whitespace from DataFrame index, columns, and string values."""
    if df.index.dtype == "object":
        df.index = df.index.str.strip()
    df.columns = df.columns.str.strip()
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].astype(str).str.strip()
            try:
                if df[col].str.isnumeric().all():
                    df[col] = pd.to_numeric(df[col])
            except:
                pass
    return df

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
    value_str = str(value).strip()
    try:
        cleaned_value = value_str.replace(',', '')
        return float(cleaned_value) if '.' in cleaned_value else int(cleaned_value)
    except (ValueError, TypeError):
        return None 