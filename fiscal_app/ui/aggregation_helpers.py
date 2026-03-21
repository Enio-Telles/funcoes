from __future__ import annotations

import traceback

import polars as pl
from PySide6.QtWidgets import QMessageBox


def open_editable_aggregation_table(window) -> None:
    if not window.state.current_cnpj:
        window.show_error("CNPJ não selecionado", "Selecione um CNPJ na lista.")
        return
    try:
        target = window.servico_agregacao.carregar_tabela_editavel(window.state.current_cnpj)
        df = pl.read_parquet(target)
        window.state.all_columns = df.columns
        window.aggregation_table_model.set_dataframe(df)
        window.aggregation_table_view.resizeColumnsToContents()
    except Exception as exc:
        window.show_error("Falha ao abrir tabela editável", str(exc))
        return
    window.state.current_file = target
    window.state.current_page = 1
    window.state.filters = []
    window.tabs.setCurrentIndex(2)


def execute_aggregation(window) -> None:
    if not window.state.current_cnpj:
        window.show_error("CNPJ não selecionado", "Selecione um CNPJ antes de agregar.")
        return

    rows_top = window.aggregation_table_model.get_checked_rows()
    rows_bottom = window.results_table_model.get_checked_rows()
    combined = []
    seen = set()
    for row in rows_top + rows_bottom:
        key = (str(row.get("descrição_normalizada") or ""), str(row.get("descricao") or ""))
        if key not in seen:
            seen.add(key)
            combined.append(row)

    if len(combined) < 2:
        window.show_error(
            "Seleção insuficiente",
            "Marque pelo menos duas linhas com 'Visto' (pode ser em ambas as tabelas) para agregar.",
        )
        return

    try:
        result = window.servico_agregacao.agregar_linhas(
            cnpj=window.state.current_cnpj,
            linhas_selecionadas=combined,
        )
        update_aggregation_tables(window)
        reload_aggregation_history(window, window.state.current_cnpj)
        window.show_info(
            "Agregação concluída",
            f"As {len(combined)} descrições foram unificadas em:\n'{result.linha_agregada['descricao']}'",
        )
    except Exception as exc:
        traceback.print_exc()
        window.show_error("Erro na agregação", f"Ocorreu um erro ao agregar: {exc}")
        window.aggregation_table_model.clear_checked()
        window.results_table_model.clear_checked()
        open_editable_aggregation_table(window)


def recalculate_aggregation_defaults(window) -> None:
    cnpj = window.state.current_cnpj
    if not cnpj:
        return

    ret = QMessageBox.question(
        window,
        "Recalcular Padrões",
        "Isso irá atualizar NCM, CEST, GTIN, UNID e SEFIN de TODOS os grupos baseando-se na moda dos itens originais.\nProsseguir?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
    )
    if ret == QMessageBox.StandardButton.No:
        return

    try:
        ok = window.servico_agregacao.recalcular_todos_padroes(cnpj)
        if ok:
            update_aggregation_tables(window)
            QMessageBox.information(window, "Sucesso", "Valores padrão recalculados com sucesso para toda a tabela.")
        else:
            QMessageBox.warning(window, "Aviso", "Não foi possível recalcular. Verifique se as tabelas existem.")
    except Exception as exc:
        QMessageBox.critical(window, "Erro", f"Erro ao recalcular: {exc}")


def recalculate_aggregation_totals(window) -> None:
    cnpj = window.state.current_cnpj
    if not cnpj:
        return

    ret = QMessageBox.question(
        window,
        "Recalcular Totais",
        "Isso irá calcular os totais de Entrada (C170) e Saída (NFe) para todos os produtos (apenas operações mercantis).\nProsseguir?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
    )
    if ret == QMessageBox.StandardButton.No:
        return

    window.status.showMessage("Calculando totais de valores...")
    try:
        ok = window.servico_agregacao.recalcular_valores_totais(cnpj)
        if ok:
            update_aggregation_tables(window)
            QMessageBox.information(window, "Sucesso", "Totais de valores recalculados com sucesso.")
        else:
            QMessageBox.warning(window, "Aviso", "Não foi possível recalcular os totais.")
    except Exception as exc:
        QMessageBox.critical(window, "Erro", f"Erro ao recalcular totais: {exc}")
    finally:
        window.status.showMessage("Pronto.")


def reload_aggregation_history(window, cnpj: str) -> None:
    historico = window.servico_agregacao.ler_linhas_log(cnpj=cnpj)
    window.results_table_model.set_dataframe(pl.DataFrame(historico))
    window.results_table_view.resizeColumnsToContents()


def update_aggregation_tables(window) -> None:
    cnpj = window.state.current_cnpj
    if not cnpj:
        return
    path = window.servico_agregacao.caminho_tabela_editavel(cnpj)
    if path.exists():
        df = pl.read_parquet(path)
        window.aggregation_table_model.set_dataframe(df)
        window.aggregation_table_view.resizeColumnsToContents()
