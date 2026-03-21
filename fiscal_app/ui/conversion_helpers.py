from __future__ import annotations

import polars as pl
from PySide6.QtWidgets import QFileDialog, QMessageBox

from fiscal_app.config import CNPJ_ROOT


def load_conversion_table(window) -> None:
    cnpj = window.state.current_cnpj
    if not cnpj:
        return

    pasta_produtos = CNPJ_ROOT / cnpj / "analises" / "produtos"
    arq_conversao = pasta_produtos / f"fatores_conversao_{cnpj}.parquet"

    if not arq_conversao.exists():
        window.conversion_model.set_dataframe(pl.DataFrame())
        return

    try:
        df = pl.read_parquet(arq_conversao)
        window.conversion_model.set_dataframe(df)
        window.conversion_table.resizeColumnsToContents()
    except Exception as exc:
        QMessageBox.warning(window, "Erro", f"Erro ao carregar fatores_conversao: {exc}")


def export_conversion_excel(window) -> None:
    df = window.conversion_model.dataframe
    if df.is_empty():
        QMessageBox.information(window, "Aviso", "Não há fatores_conversao para exportar.")
        return

    path, _ = QFileDialog.getSaveFileName(
        window,
        "Salvar Excel",
        f"fatores_conversao_{window.state.current_cnpj}.xlsx",
        "Excel (*.xlsx)",
    )
    if not path:
        return

    try:
        df.write_excel(path)
        QMessageBox.information(window, "Sucesso", f"Planilha de revisão salva com sucesso:\n{path}")
    except Exception as exc:
        QMessageBox.critical(window, "Erro", f"Erro ao exportar: {exc}")


def import_conversion_excel(window) -> None:
    cnpj = window.state.current_cnpj
    if not cnpj:
        return

    path, _ = QFileDialog.getOpenFileName(window, "Abrir Excel", "", "Excel (*.xlsx)")
    if not path:
        return

    try:
        df_excel = pl.read_excel(path)
        obrigatorias = {"id_produtos", "unid", "fator"}
        if not obrigatorias.issubset(set(df_excel.columns)):
            raise ValueError(
                "O Excel deve conter as colunas: id_produtos, unid, fator. A coluna unid_ref é opcional."
            )

        if "unid_ref" not in df_excel.columns:
            df_excel = df_excel.with_columns(pl.lit(None, dtype=pl.String).alias("unid_ref"))

        df_imp = df_excel.select(["id_produtos", "unid", "unid_ref", "fator"]).with_columns(
            [
                pl.col("id_produtos").cast(pl.String),
                pl.col("unid").cast(pl.String),
                pl.col("unid_ref").cast(pl.String),
                pl.col("fator").cast(pl.Float64),
            ]
        )

        pasta_produtos = CNPJ_ROOT / cnpj / "analises" / "produtos"
        nome_saida = f"fatores_conversao_manuais_{cnpj}.parquet"
        df_imp.write_parquet(pasta_produtos / nome_saida)

        QMessageBox.information(
            window,
            "Sucesso",
            "Revisões manuais importadas com sucesso.\n"
            f"Arquivo salvo em: {nome_saida}\n\n"
            "Reexecute o pipeline oficial ou recalcule os fatores para aplicar as revisões.",
        )
    except Exception as exc:
        QMessageBox.critical(window, "Erro", f"Erro ao importar revisões: {exc}")
