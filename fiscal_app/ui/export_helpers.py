from __future__ import annotations

from pathlib import Path

import polars as pl
from PySide6.QtWidgets import QFileDialog

from fiscal_app.config import CONSULTAS_ROOT


def save_dialog(window, title: str, pattern: str) -> Path | None:
    filename, _ = QFileDialog.getSaveFileName(window, title, str(CONSULTAS_ROOT), pattern)
    return Path(filename) if filename else None


def filters_text(window) -> str:
    return " | ".join(f"{f.column} {f.operator} {f.value}".strip() for f in window.state.filters or [])


def dataset_for_export(window, mode: str) -> pl.DataFrame:
    if window.state.current_file is None:
        raise ValueError("Nenhum arquivo selecionado.")
    if mode == "full":
        return window.parquet_service.load_dataset(window.state.current_file)
    if mode == "filtered":
        return window.parquet_service.load_dataset(window.state.current_file, window.state.filters or [])
    if mode == "visible":
        return window.parquet_service.load_dataset(
            window.state.current_file,
            window.state.filters or [],
            window.state.visible_columns or [],
        )
    raise ValueError(f"Modo de exportação não suportado: {mode}")


def export_excel(window, mode: str) -> None:
    try:
        df = dataset_for_export(window, mode)
        target = save_dialog(window, "Salvar Excel", "Excel (*.xlsx)")
        if not target:
            return
        window.export_service.export_excel(
            target,
            df,
            sheet_name=window.state.current_file.stem if window.state.current_file else "Dados",
        )
        window.show_info("Exportação concluída", f"Arquivo gerado em:\n{target}")
    except Exception as exc:
        window.show_error("Falha na exportação para Excel", str(exc))


def export_docx(window) -> None:
    try:
        if window.state.current_file is None:
            raise ValueError("Nenhum arquivo selecionado.")
        df = window.parquet_service.load_dataset(
            window.state.current_file,
            window.state.filters or [],
            window.state.visible_columns or [],
        )
        target = save_dialog(window, "Salvar relatório Word", "Word (*.docx)")
        if not target:
            return
        window.export_service.export_docx(
            target,
            title="Relatório Padronizado de Análise Fiscal",
            cnpj=window.state.current_cnpj or "",
            table_name=window.state.current_file.name,
            df=df,
            filters_text=filters_text(window),
            visible_columns=window.state.visible_columns or [],
        )
        window.show_info("Relatório gerado", f"Arquivo gerado em:\n{target}")
    except Exception as exc:
        window.show_error("Falha na exportação para Word", str(exc))


def export_txt_html(window) -> None:
    try:
        if window.state.current_file is None:
            raise ValueError("Nenhum arquivo selecionado.")
        df = window.parquet_service.load_dataset(
            window.state.current_file,
            window.state.filters or [],
            window.state.visible_columns or [],
        )
        html_report = window.export_service.build_html_report(
            title="Relatório Padronizado de Análise Fiscal",
            cnpj=window.state.current_cnpj or "",
            table_name=window.state.current_file.name,
            df=df,
            filters_text=filters_text(window),
            visible_columns=window.state.visible_columns or [],
        )
        target = save_dialog(window, "Salvar TXT com HTML", "TXT (*.txt)")
        if not target:
            return
        window.export_service.export_txt_with_html(target, html_report)
        window.show_info("Relatório HTML/TXT gerado", f"Arquivo gerado em:\n{target}")
    except Exception as exc:
        window.show_error("Falha na exportação TXT/HTML", str(exc))
