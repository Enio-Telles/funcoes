from __future__ import annotations

from fiscal_app.services.parquet_service import FilterCondition
from fiscal_app.ui.dialogs import ColumnSelectorDialog
from fiscal_app.utils.text import remove_accents


def add_filter_from_form(window) -> None:
    column = window.filter_column.currentText().strip()
    operator = window.filter_operator.currentText().strip()
    value = window.filter_value.text().strip()

    if not column:
        window.show_error("Filtro inválido", "Selecione uma coluna para filtrar.")
        return
    if operator not in {"é nulo", "não é nulo"} and value == "":
        window.show_error("Filtro inválido", "Informe um valor para o filtro escolhido.")
        return

    window.state.filters = window.state.filters or []
    window.state.filters.append(FilterCondition(column=column, operator=operator, value=value))
    window.state.current_page = 1
    window.filter_value.clear()
    window.reload_table()


def clear_filters(window) -> None:
    window.state.filters = []
    window.state.current_page = 1
    window.reload_table()


def remove_selected_filter(window) -> None:
    row = window.filter_list.currentRow()
    if row < 0 or not window.state.filters:
        return
    window.state.filters.pop(row)
    window.state.current_page = 1
    window.reload_table()


def choose_columns(window) -> None:
    if not window.state.all_columns:
        return

    dialog = ColumnSelectorDialog(
        window.state.all_columns,
        window.state.visible_columns or window.state.all_columns,
        window,
    )
    if dialog.exec():
        selected = dialog.selected_columns()
        if not selected:
            window.show_error("Seleção inválida", "Pelo menos uma coluna deve permanecer visível.")
            return
        window.state.visible_columns = selected
        window.state.current_page = 1
        window.reload_table()


def prev_page(window) -> None:
    if window.state.current_page > 1:
        window.state.current_page -= 1
        window.reload_table()


def next_page(window) -> None:
    total_pages = max(
        1,
        ((window.state.total_rows - 1) // window.state.page_size) + 1 if window.state.total_rows else 1,
    )
    if window.state.current_page < total_pages:
        window.state.current_page += 1
        window.reload_table()


def apply_quick_filters(window) -> None:
    idx = window.tabs.currentIndex()
    if idx == 0:
        fields = {
            "descricao_normalizada": window.qf_norm.text().strip(),
            "descricao": window.qf_desc.text().strip(),
            "ncm_padrao": window.qf_ncm.text().strip(),
            "cest_padrao": window.qf_cest.text().strip(),
        }
    elif idx == 2:
        fields = {
            "descricao_normalizada": window.aqf_norm.text().strip(),
            "descricao": window.aqf_desc.text().strip(),
            "ncm_padrao": window.aqf_ncm.text().strip(),
            "cest_padrao": window.aqf_cest.text().strip(),
        }
    else:
        return

    quick_cols = set(fields.keys())
    new_filters = [f for f in (window.state.filters or []) if f.column not in quick_cols]

    for col, val in fields.items():
        if not val:
            continue
        actual_col = col
        if window.state.all_columns:
            alternatives = {
                "ncm_padrao": ["ncm_padrao", "NCM_padrao", "lista_ncm"],
                "cest_padrao": ["cest_padrao", "CEST_padrao", "lista_cest"],
                "descricao_normalizada": ["descricao_normalizada", "descricao", "descr_norm"],
                "descricao": ["descricao", "lista_descricoes", "descr"],
            }
            if col in alternatives:
                for alt in alternatives[col]:
                    if alt in window.state.all_columns:
                        actual_col = alt
                        break
            elif col not in window.state.all_columns:
                target_clean = remove_accents(col).lower()
                for current_col in window.state.all_columns:
                    if remove_accents(current_col).lower() == target_clean:
                        actual_col = current_col
                        break
        new_filters.append(FilterCondition(column=actual_col, operator="contém", value=val))

    window.state.filters = new_filters
    window.state.current_page = 1
    window.reload_table(update_main_view=(idx == 0))
    if idx == 2:
        window.aggregation_table_model.set_dataframe(window.current_page_df_all)
        window.aggregation_table_view.resizeColumnsToContents()
