from __future__ import annotations

from pathlib import Path

import polars as pl
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTreeWidgetItem


def refresh_file_tree(window, cnpj: str) -> None:
    window.file_tree.clear()
    root_path = window.parquet_service.cnpj_dir(cnpj)

    cat_brutas = QTreeWidgetItem(["Tabelas brutas (SQL)", str(root_path / "arquivos_parquet")])
    cat_analises = QTreeWidgetItem(["Análises de Produtos", str(root_path / "analises" / "produtos")])
    cat_outros = QTreeWidgetItem(["Outros Parquets", str(root_path)])
    window.file_tree.addTopLevelItem(cat_brutas)
    window.file_tree.addTopLevelItem(cat_analises)
    window.file_tree.addTopLevelItem(cat_outros)

    first_leaf: QTreeWidgetItem | None = None
    for path in window.parquet_service.list_parquet_files(cnpj):
        if "arquivos_parquet" in str(path.parent):
            parent = cat_brutas
        elif "analises" in str(path.parent) or "produtos" in str(path.parent):
            parent = cat_analises
        else:
            parent = cat_outros

        item = QTreeWidgetItem([path.name, str(path.parent)])
        item.setData(0, Qt.UserRole, str(path))
        parent.addChild(item)
        if first_leaf is None:
            first_leaf = item

    cat_brutas.setExpanded(True)
    cat_analises.setExpanded(True)
    for cat in [cat_brutas, cat_analises, cat_outros]:
        if cat.childCount() == 0:
            window.file_tree.takeTopLevelItem(window.file_tree.indexOfTopLevelItem(cat))

    if first_leaf is not None:
        window.file_tree.setCurrentItem(first_leaf)
        on_file_activated(window, first_leaf, 0)


def on_file_activated(window, item: QTreeWidgetItem, _column: int) -> None:
    raw_path = item.data(0, Qt.UserRole)
    if not raw_path:
        return
    window.state.current_file = Path(raw_path)
    window.state.current_page = 1
    window.state.filters = []
    window.current_page_df_all = pl.DataFrame()
    window.current_page_df_visible = pl.DataFrame()
    load_current_file(window, reset_columns=True)
    window.tabs.setCurrentIndex(0)


def load_current_file(window, reset_columns: bool = False) -> None:
    if window.state.current_file is None:
        return
    try:
        all_columns = window.parquet_service.get_schema(window.state.current_file)
    except Exception as exc:
        window.show_error("Erro ao abrir Parquet", str(exc))
        return

    window.state.all_columns = all_columns
    if reset_columns or not window.state.visible_columns:
        window.state.visible_columns = all_columns[:]
    window.filter_column.clear()
    window.filter_column.addItems(all_columns)
    reload_table(window)


def reload_table(window, update_main_view: bool = True) -> None:
    if window.state.current_file is None:
        return
    try:
        page_result = window.parquet_service.get_page(
            window.state.current_file,
            window.state.filters or [],
            window.state.visible_columns or [],
            window.state.current_page,
            window.state.page_size,
        )
        window.state.total_rows = page_result.total_rows
        window.current_page_df_all = page_result.df_all_columns
        window.current_page_df_visible = page_result.df_visible
        if update_main_view:
            window.table_model.set_dataframe(window.current_page_df_visible)
            update_page_label(window)
            update_context_label(window)
            refresh_filter_list_widget(window)
            window.table_view.resizeColumnsToContents()
    except Exception as exc:
        window.show_error("Erro ao carregar dados", str(exc))


def update_page_label(window) -> None:
    total_pages = max(1, ((window.state.total_rows - 1) // window.state.page_size) + 1 if window.state.total_rows else 1)
    if window.state.current_page > total_pages:
        window.state.current_page = total_pages
    window.lbl_page.setText(
        f"Página {window.state.current_page}/{total_pages} | Linhas filtradas: {window.state.total_rows}"
    )


def update_context_label(window) -> None:
    if window.state.current_file is None:
        window.lbl_context.setText("Nenhum arquivo selecionado")
        return
    window.lbl_context.setText(
        f"CNPJ: {window.state.current_cnpj or '-'} | Arquivo: {window.state.current_file.name} | "
        f"Colunas visíveis: {len(window.state.visible_columns or [])}/{len(window.state.all_columns or [])}"
    )


def refresh_filter_list_widget(window) -> None:
    window.filter_list.clear()
    for cond in window.state.filters or []:
        window.filter_list.addItem(f"{cond.column} {cond.operator} {cond.value}".strip())
