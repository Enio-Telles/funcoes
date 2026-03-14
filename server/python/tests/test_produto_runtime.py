from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import polars as pl


SERVER_PYTHON_DIR = Path(__file__).resolve().parents[1]
if str(SERVER_PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_PYTHON_DIR))

from core.produto_runtime import (  # noqa: E402
    _DETAIL_COLUMNS,
    _aplicar_mapas_manuais,
    _build_codigos_multidescricao,
    _build_produtos_agregados,
    _build_produtos_indexados,
    _build_variacoes_produtos,
)


def _base_df() -> pl.DataFrame:
    rows = [
        {
            "fonte": "C170",
            "codigo": "001",
            "descricao": "ARROZ TIPO 1",
            "descr_compl": "PACOTE 5KG",
            "tipo_item": "00",
            "ncm": "10063021",
            "cest": "",
            "gtin": "789000000001",
            "unid": "UN",
            "codigo_original": "001",
            "descricao_original": "ARROZ TIPO 1",
            "tipo_item_original": "00",
            "hash_manual_key": "hash-a",
        },
        {
            "fonte": "NFE",
            "codigo": "001",
            "descricao": "ARROZ TIPO 1",
            "descr_compl": "PACOTE 1KG",
            "tipo_item": "00",
            "ncm": "10063021",
            "cest": "",
            "gtin": "789000000001",
            "unid": "FD",
            "codigo_original": "001",
            "descricao_original": "ARROZ TIPO 1",
            "tipo_item_original": "00",
            "hash_manual_key": "hash-b",
        },
        {
            "fonte": "REG0200",
            "codigo": "002",
            "descricao": "FEIJAO CARIOCA",
            "descr_compl": "",
            "tipo_item": "00",
            "ncm": "07133319",
            "cest": "",
            "gtin": "789000000002",
            "unid": "UN",
            "codigo_original": "002",
            "descricao_original": "FEIJAO CARIOCA",
            "tipo_item_original": "00",
            "hash_manual_key": "hash-c",
        },
        {
            "fonte": "NFCe",
            "codigo": "002A",
            "descricao": "FEIJAO CARIOCA",
            "descr_compl": "PREMIUM",
            "tipo_item": "00",
            "ncm": "07133319",
            "cest": "",
            "gtin": "789000000099",
            "unid": "UN",
            "codigo_original": "002A",
            "descricao_original": "FEIJAO CARIOCA",
            "tipo_item_original": "00",
            "hash_manual_key": "hash-d",
        },
    ]
    return pl.DataFrame(rows).select(_DETAIL_COLUMNS)


class ProdutoRuntimeBuildersTests(unittest.TestCase):
    def test_build_produtos_agregados_group_by_descricao(self) -> None:
        df = _build_produtos_agregados(_base_df())

        self.assertEqual(df.height, 2)
        arroz = df.filter(pl.col("descricao") == "ARROZ TIPO 1").to_dicts()[0]
        feijao = df.filter(pl.col("descricao") == "FEIJAO CARIOCA").to_dicts()[0]

        self.assertEqual(arroz["qtd_codigos"], 1)
        self.assertFalse(arroz["requer_revisao_manual"])
        self.assertEqual(arroz["lista_unid"], "FD, UN")

        self.assertEqual(feijao["qtd_codigos"], 2)
        self.assertTrue(feijao["requer_revisao_manual"])
        self.assertIn("CODIGO", feijao["descricoes_conflitantes"])
        self.assertIn("GTIN", feijao["descricoes_conflitantes"])

    def test_build_produtos_indexados_and_codigos_multidescricao(self) -> None:
        df_base = _base_df()
        df_agregados = _build_produtos_agregados(df_base)
        df_indexados = _build_produtos_indexados(df_base, df_agregados)
        df_codigos = _build_codigos_multidescricao(df_indexados)

        self.assertEqual(df_indexados.height, 4)
        self.assertEqual(df_codigos.height, 0)

        duplicated = pl.concat(
            [
                df_indexados,
                pl.DataFrame(
                    [
                        {
                            "chave_produto": "ID_0003",
                            "codigo": "009",
                            "descricao": "CAFE TORRADO",
                            "descr_compl": "250G",
                            "tipo_item": "00",
                            "ncm": "09012100",
                            "cest": "",
                            "gtin": "789000000300",
                            "lista_unidades": "UN",
                            "lista_fontes": "C170",
                            "qtd_linhas": 1,
                        },
                        {
                            "chave_produto": "ID_0004",
                            "codigo": "009",
                            "descricao": "CAFE SUPERIOR",
                            "descr_compl": "250G",
                            "tipo_item": "00",
                            "ncm": "09012100",
                            "cest": "",
                            "gtin": "789000000301",
                            "lista_unidades": "UN",
                            "lista_fontes": "NFE",
                            "qtd_linhas": 1,
                        },
                    ]
                ),
            ],
            how="diagonal_relaxed",
        )
        df_codigos = _build_codigos_multidescricao(duplicated)
        row = df_codigos.filter(pl.col("codigo") == "009").to_dicts()[0]

        self.assertEqual(row["qtd_descricoes"], 2)
        self.assertEqual(row["qtd_grupos_descricao_afetados"], 2)
        self.assertIn("CAFE TORRADO", row["lista_descricoes"])
        self.assertIn("250G", row["lista_descr_compl"])

    def test_build_variacoes_produtos_flags_description_variations(self) -> None:
        df_variacoes = _build_variacoes_produtos(_base_df())
        row = df_variacoes.filter(pl.col("descricao") == "FEIJAO CARIOCA").to_dicts()[0]
        self.assertEqual(row["qtd_codigos"], 2)
        self.assertEqual(row["qtd_gtin"], 2)

    def test_aplicar_mapas_manuais_unifies_descriptions_and_overrides_item(self) -> None:
        df_base = _base_df()
        with tempfile.TemporaryDirectory() as tmp:
            dir_analises = Path(tmp)
            pl.DataFrame(
                [
                    {
                        "tipo_regra": "UNIR_GRUPOS",
                        "descricao_origem": "FEIJAO CARIOCA",
                        "descricao_destino": "FEIJAO CANONICO",
                        "descricao_par": "",
                        "hash_descricoes_key": "",
                        "chave_grupo_a": "",
                        "chave_grupo_b": "",
                        "score_origem": "",
                        "acao_manual": "AGREGAR",
                    }
                ]
            ).write_parquet(str(dir_analises / "mapa_manual_descricoes_123.parquet"))
            pl.DataFrame(
                [
                    {
                        "fonte": "NFCE",
                        "codigo_original": "002A",
                        "descricao_original": "FEIJAO CARIOCA",
                        "tipo_item_original": "00",
                        "hash_manual_key": "hash-d",
                        "codigo_novo": "002B",
                        "descricao_nova": "FEIJAO ESPECIAL",
                        "ncm_novo": "07133319",
                        "cest_novo": "",
                        "gtin_novo": "789000000555",
                        "tipo_item_novo": "01",
                        "acao_manual": "AGREGAR",
                    }
                ]
            ).write_parquet(str(dir_analises / "mapa_manual_unificacao_123.parquet"))

            applied = _aplicar_mapas_manuais(df_base, dir_analises, "123")

        manual_row = applied.filter(pl.col("hash_manual_key") == "hash-d").to_dicts()[0]
        other_row = applied.filter(pl.col("hash_manual_key") == "hash-c").to_dicts()[0]

        self.assertEqual(manual_row["codigo"], "002B")
        self.assertEqual(manual_row["descricao"], "FEIJAO ESPECIAL")
        self.assertEqual(manual_row["gtin"], "789000000555")
        self.assertEqual(manual_row["tipo_item"], "01")
        self.assertEqual(other_row["descricao"], "FEIJAO CANONICO")


if __name__ == "__main__":
    unittest.main()
