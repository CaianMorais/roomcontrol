import re
from validate_docbr import CNPJ

_cnpj = CNPJ()

def only_digits(s: str) -> str:
    """Remove all non-digit characters from a string."""
    return re.sub(r'\D', '', s or '')

def is_valid_cnpj(cnpj: str) -> bool:
    """Check if a CNPJ number is valid."""
    cnpj = only_digits(cnpj)
    return _cnpj.validate(cnpj)

def format_cnpj(cnpj: str) -> str:
    """Format a CNPJ number to the standard format."""
    cnpj = only_digits(cnpj)
    return _cnpj.mask(cnpj)