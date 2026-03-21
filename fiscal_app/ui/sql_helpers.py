from __future__ import annotations

from pathlib import Path

import polars as pl
from PySide6.QtCore import QDate
from PySide6.QtWidgets import QDateEdit, QLabel, QLineEdit

from fiscal_app.services.query_worker import QueryWorker
from fiscal_app.services.sql_service import WIDGET_DATE


def populate_sql_combo(window) -> None:
    window._sql_files = window.sql_service.list_sql_files()
    window.sql_combo.blockSignals(True)
    window.sql_combo.clear()
    window.sql_combo.addItem("— Selecione uma consulta —")
    for info in window._sql_files:
        window.sql_combo.addItem(f"{info.display_name}  [{info.source_dir}]", str(info.path))
    window.sql_combo.blockSignals(False)


def on_sql_selected(window, index: int) -> None:
    if index <= 0:
        window.sql_text_view.setPlainText("")
        clear_param_form(window)
        window._sql_current_sql = ""
        return

    path_str = window.sql_combo.itemData(index)
    if not path_str:
        return

    try:
        sql_text = window.sql_service.read_sql(Path(path_str))
    except Exception as exc:
        window.show_error("Erro ao ler SQL", str(exc))
        return

    window._sql_current_sql = sql_text
    window.sql_text_view.setPlainText(sql_text)
    params = window.sql_service.extract_params(sql_text)
    rebuild_param_form(window, params)


def clear_param_form(window) -> None:
    while window.sql_param_form.rowCount() > 0:
        window.sql_param_form.removeRow(0)
    window._sql_param_widgets.clear()


def rebuild_param_form(window, params) -> None:
    clear_param_form(window)
    for param in params:
        label = QLabel(f":{param.name}")
        label.setStyleSheet("font-weight: bold; color: #1e40af;")
        if param.widget_type == WIDGET_DATE:
            widget = QDateEdit()
            widget.setCalendarPopup(True)
            widget.setDate(QDate.currentDate())
            widget.setDisplayFormat("dd/MM/yyyy")
        else:
            widget = QLineEdit()
            if param.placeholder:
                widget.setPlaceholderText(param.placeholder)
            if "cnpj" in param.name.lower() and window.state.current_cnpj:
                widget.setText(window.state.current_cnpj)
        window.sql_param_form.addRow(label, widget)
        window._sql_param_widgets[param.name] = widget


def collect_param_values(window) -> dict[str, str]:
    values: dict[str, str] = {}
    for name, widget in window._sql_param_widgets.items():
        if isinstance(widget, QDateEdit):
            values[name] = widget.date().toString("dd/MM/yyyy")
        elif isinstance(widget, QLineEdit):
            values[name] = widget.text().strip()
        else:
            values[name] = ""
    return values


def execute_sql_query(window) -> None:
    if not window._sql_current_sql:
        window.show_error("Nenhum SQL", "Selecione um arquivo SQL antes de executar.")
        return
    if window.query_worker is not None and window.query_worker.isRunning():
        window.show_error("Aguarde", "Uma consulta já está em execução.")
        return

    values = collect_param_values(window)
    binds = window.sql_service.build_binds(window._sql_current_sql, values)
    window.btn_sql_execute.setEnabled(False)
    set_sql_status(window, "⏳ Conectando ao Oracle...", "#fef9c3", "#92400e")

    window.query_worker = QueryWorker(window._sql_current_sql, binds)
    window.query_worker.progress.connect(lambda msg: set_sql_status(window, f"⏳ {msg}", "#fef9c3", "#92400e"))
    window.query_worker.finished_ok.connect(lambda df: on_query_finished(window, df))
    window.query_worker.failed.connect(lambda message: on_query_failed(window, message))
    window.query_worker.start()


def on_query_finished(window, df: pl.DataFrame) -> None:
    window.btn_sql_execute.setEnabled(True)
    window._sql_result_df = df
    window._sql_result_page = 1
    if df.height == 0:
        set_sql_status(window, "ℹ️  Consulta retornou 0 resultados.", "#e0e7ff", "#3730a3")
        window.sql_result_model.set_dataframe(pl.DataFrame())
    else:
        set_sql_status(window, f"✅ {df.height:,} linhas, {df.width} colunas.", "#dcfce7", "#166534")
        show_sql_result_page(window)


def on_query_failed(window, message: str) -> None:
    window.btn_sql_execute.setEnabled(True)
    set_sql_status(window, f"❌ Erro: {message[:200]}", "#fee2e2", "#991b1b")


def set_sql_status(window, text: str, bg: str, fg: str) -> None:
    window.sql_status_label.setText(text)
    window.sql_status_label.setStyleSheet(
        f"QLabel {{ padding: 4px 8px; background: {bg}; border-radius: 4px; border: 1px solid {bg}; color: {fg}; font-weight: bold; }}"
    )


def show_sql_result_page(window) -> None:
    df = window._sql_result_df
    if df.height == 0:
        return
    total_pages = max(1, ((df.height - 1) // window._sql_result_page_size) + 1)
    window._sql_result_page = max(1, min(window._sql_result_page, total_pages))
    offset = (window._sql_result_page - 1) * window._sql_result_page_size
    page_df = df.slice(offset, window._sql_result_page_size)
    window.sql_result_model.set_dataframe(page_df)
    window.sql_result_table.resizeColumnsToContents()
    window.sql_result_page_label.setText(f"Página {window._sql_result_page}/{total_pages} | Total: {df.height:,}")


def sql_prev_page(window) -> None:
    if window._sql_result_page > 1:
        window._sql_result_page -= 1
        show_sql_result_page(window)


def sql_next_page(window) -> None:
    total_pages = max(1, ((window._sql_result_df.height - 1) // window._sql_result_page_size) + 1)
    if window._sql_result_page < total_pages:
        window._sql_result_page += 1
        show_sql_result_page(window)


def filter_sql_results(window) -> None:
    search = window.sql_result_search.text().strip().lower()
    if not search or window._sql_result_df.height == 0:
        window._sql_result_page = 1
        show_sql_result_page(window)
        return

    exprs = [
        pl.col(c).cast(pl.Utf8, strict=False).fill_null("").str.to_lowercase().str.contains(search, literal=True)
        for c in window._sql_result_df.columns
    ]
    combined = exprs[0]
    for expr in exprs[1:]:
        combined = combined | expr
    filtered = window._sql_result_df.filter(combined)

    if filtered.height == 0:
        set_sql_status(window, f"ℹ️  Busca '{search}' não encontrou resultados.", "#e0e7ff", "#3730a3")
        window.sql_result_model.set_dataframe(pl.DataFrame())
    else:
        set_sql_status(window, f"✅ Busca '{search}': {filtered.height:,} de {window._sql_result_df.height:,} linhas.", "#dcfce7", "#166534")
        page_df = filtered.head(window._sql_result_page_size)
        window.sql_result_model.set_dataframe(page_df)
        window.sql_result_table.resizeColumnsToContents()
        total_pages = max(1, ((filtered.height - 1) // window._sql_result_page_size) + 1)
        window.sql_result_page_label.setText(f"Página 1/{total_pages} | Filtrado: {filtered.height:,}")


def export_sql_results(window) -> None:
    if window._sql_result_df.height == 0:
        window.show_error("Sem dados", "Execute uma consulta antes de exportar.")
        return

    target = window._save_dialog("Exportar resultados SQL para Excel", "Excel (*.xlsx)")
    if not target:
        return

    try:
        sql_name = window.sql_combo.currentText().split("[")[0].strip() or "consulta_sql"
        window.export_service.export_excel(target, window._sql_result_df, sheet_name=sql_name[:31])
        window.show_info("Exportação concluída", f"Arquivo gerado em:\n{target}")
    except Exception as exc:
        window.show_error("Falha na exportação", str(exc))
