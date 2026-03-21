from __future__ import annotations

from pathlib import Path

import polars as pl

from fiscal_app.config import CNPJ_ROOT


def traceability_files(cnpj: str | None) -> dict[str, Path]:
    cnpj = cnpj or ""
    pasta = CNPJ_ROOT / cnpj / "analises" / "produtos"
    return {
        "origens_brutas": pasta / f"produtos_unidades_origens_{cnpj}.parquet",
        "mapa_produtos": pasta / f"produtos_origens_{cnpj}.parquet",
        "rastro_agrupamento": pasta / f"produtos_agrupados_rastro_{cnpj}.parquet",
        "origens_agrupamento": pasta / f"produtos_final_origens_{cnpj}.parquet",
        "auditoria_fatores": pasta / f"fatores_conversao_auditoria_{cnpj}.parquet",
        "precos_fatores": pasta / f"fatores_conversao_precos_{cnpj}.parquet",
    }


def clear_traceability_state(window) -> None:
    window._trace_df = pl.DataFrame()
    window.trace_model.set_dataframe(pl.DataFrame())
    window.trace_status_label.setText("Nenhum arquivo de rastreabilidade carregado.")
    window.trace_filter_id_agrupado.clear()
    window.trace_filter_chave_produto.clear()


def open_traceability_file(window, path: Path, titulo: str) -> None:
    if not window.state.current_cnpj:
        window.show_error("CNPJ não selecionado", "Selecione um CNPJ para abrir a rastreabilidade.")
        return
    if not path.exists():
        window.show_error("Arquivo não encontrado", f"Arquivo de rastreabilidade ausente:\n{path.name}")
        return
    try:
        df = pl.read_parquet(path)
        window._trace_df = df
        window.trace_model.set_dataframe(df)
        window.trace_table.resizeColumnsToContents()
        window.trace_status_label.setText(f"{titulo}: {path.name} | {df.height:,} linhas")
        window.tabs.setCurrentWidget(window.trace_tab)
    except Exception as exc:
        window.show_error("Erro ao abrir rastreabilidade", str(exc))


def filter_trace_df(window, df: pl.DataFrame) -> pl.DataFrame:
    id_agr = window.trace_filter_id_agrupado.text().strip().lower()
    chave = window.trace_filter_chave_produto.text().strip().lower()
    out = df
    if id_agr and "id_agrupado" in out.columns:
        out = out.filter(
            pl.col("id_agrupado")
            .cast(pl.Utf8, strict=False)
            .fill_null("")
            .str.to_lowercase()
            .str.contains(id_agr, literal=True)
        )
    if chave and "chave_produto" in out.columns:
        out = out.filter(
            pl.col("chave_produto")
            .cast(pl.Utf8, strict=False)
            .fill_null("")
            .str.to_lowercase()
            .str.contains(chave, literal=True)
        )
    return out


def apply_traceability_filter(window) -> None:
    if window._trace_df.is_empty():
        return
    filtrado = filter_trace_df(window, window._trace_df)
    window.trace_model.set_dataframe(filtrado)
    window.trace_table.resizeColumnsToContents()
    window.trace_status_label.setText(f"Rastreabilidade filtrada: {filtrado.height:,} linhas")


def clear_traceability_filter(window) -> None:
    window.trace_filter_id_agrupado.clear()
    window.trace_filter_chave_produto.clear()
    if window._trace_df.is_empty():
        window.trace_model.set_dataframe(pl.DataFrame())
        window.trace_status_label.setText("Nenhum arquivo de rastreabilidade carregado.")
    else:
        window.trace_model.set_dataframe(window._trace_df)
        window.trace_table.resizeColumnsToContents()
        window.trace_status_label.setText(f"Rastreabilidade: {window._trace_df.height:,} linhas")
