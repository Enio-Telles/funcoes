import polars as pl
from src.servicos.export_service import ExportService

def test_iter_rows():
    df = pl.DataFrame({
        "int_col": pl.Series([1, 2, None], dtype=pl.Int64),
        "str_col": pl.Series(["a", "b", None], dtype=pl.String),
        "bool_col": pl.Series([True, False, None], dtype=pl.Boolean),
        "list_col": pl.Series([["1", "2"], ["x"], None], dtype=pl.List(pl.String))
    })

    expected = [
        ("1", "a", "true", "1, 2"),
        ("2", "b", "false", "x"),
        ("", "", "", "")
    ]

    service = ExportService()
    result = list(service._iter_rows(df))

    assert result == expected

def test_iter_rows_empty():
    df = pl.DataFrame({
        "int_col": pl.Series([], dtype=pl.Int64),
        "str_col": pl.Series([], dtype=pl.String)
    })

    service = ExportService()
    result = list(service._iter_rows(df))

    assert result == []
