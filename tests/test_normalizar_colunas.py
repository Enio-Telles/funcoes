import pytest
import polars as pl
from server.python.core.utils import normalizar_colunas

def test_normalizar_colunas_mixed_case():
    df = pl.DataFrame({
        "Nome": ["Alice", "Bob"],
        "IDADE": [30, 25],
        "cidade_Natal": ["SP", "RJ"]
    })
    result = normalizar_colunas(df)
    assert result.columns == ["nome", "idade", "cidade_natal"]
    assert result.shape == (2, 3)

def test_normalizar_colunas_already_lowercase():
    df = pl.DataFrame({
        "nome": ["Alice"],
        "idade": [30]
    })
    result = normalizar_colunas(df)
    assert result.columns == ["nome", "idade"]
    assert result.shape == (1, 2)

def test_normalizar_colunas_empty_dataframe():
    df = pl.DataFrame({"COLUNA": []})
    # Since the dataframe is empty, the function currently returns it without renaming, based on:
    # if df is not None and not df.is_empty():
    result = normalizar_colunas(df)
    assert result.columns == ["COLUNA"]

def test_normalizar_colunas_none():
    result = normalizar_colunas(None)
    assert result is None
