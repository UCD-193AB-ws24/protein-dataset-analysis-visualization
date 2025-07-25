from enum import Enum

class OrientationType(Enum):
    """Valid orientation values for coordinate files."""
    PLUS = "plus"
    MINUS = "minus"

    @classmethod
    def get_valid_inputs(cls):
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