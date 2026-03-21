import pytest
from server.python.core.utils import validar_cnpj

def test_validar_cnpj_valid_format():
    """Test valid CNPJs with punctuation."""
    assert validar_cnpj('00.000.000/0001-91') is True
    assert validar_cnpj('60.701.190/0001-04') is True
    assert validar_cnpj('60.746.948/0001-12') is True

def test_validar_cnpj_valid_unformatted():
    """Test valid CNPJs without punctuation."""
    assert validar_cnpj('00000000000191') is True
    assert validar_cnpj('60701190000104') is True
    assert validar_cnpj('60746948000112') is True

def test_validar_cnpj_invalid_length():
    """Test CNPJs with invalid length."""
    assert validar_cnpj('00.000.000/0001') is False  # Too short
    assert validar_cnpj('123') is False              # Too short
    assert validar_cnpj('00.000.000/0001-911') is False # Too long
    assert validar_cnpj('000000000001911') is False  # Too long
    assert validar_cnpj('') is False                 # Empty

def test_validar_cnpj_repeated_digits():
    """Test CNPJs consisting of identical digits."""
    assert validar_cnpj('00.000.000/0000-00') is False
    assert validar_cnpj('11.111.111/1111-11') is False
    assert validar_cnpj('22.222.222/2222-22') is False
    assert validar_cnpj('99.999.999/9999-99') is False
    assert validar_cnpj('00000000000000') is False
    assert validar_cnpj('11111111111111') is False

def test_validar_cnpj_invalid_check_digits():
    """Test CNPJs with incorrect check digits."""
    # Last digit wrong
    assert validar_cnpj('00.000.000/0001-92') is False
    assert validar_cnpj('60.701.190/0001-05') is False

    # First check digit wrong
    assert validar_cnpj('00.000.000/0001-01') is False
    assert validar_cnpj('60.701.190/0001-14') is False

    # Both wrong
    assert validar_cnpj('00.000.000/0001-00') is False

def test_validar_cnpj_non_numeric_characters():
    """Test CNPJs with non-numeric characters (should be removed by regex, but still valid if math matches)."""
    assert validar_cnpj('00!000@000#0001$91') is True  # Letters/symbols should be stripped
    assert validar_cnpj('A0.0B0.0C0/00D1-91E') is False # Stripping leaves '0000000191', length 10 != 14
