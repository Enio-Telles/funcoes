from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import polars as pl
from PySide6.QtCore import QDate, QThread, Qt, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDateEdit,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QScrollArea,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTableView,
    QTreeWidget,
    QVBoxLayout,
    QWidget,
)

from fiscal_app.config import APP_NAME, CNPJ_ROOT, DEFAULT_PAGE_SIZE
from fiscal_app.models.table_model import PolarsTableModel
from fiscal_app.services.aggregation_service import ServicoAgregacao
from fiscal_app.services.export_service import ExportService
from fiscal_app.services.parquet_service import FilterCondition, ParquetService
from fiscal_app.services.pipeline_funcoes_service import ResultadoPipeline, ServicoPipelineCompleto
from fiscal_app.services.query_worker import QueryWorker
from fiscal_app.services.registry_service import RegistryService
from fiscal_app.services.sql_service import SqlService
from fiscal_app.ui.aggregation_helpers import (
    execute_aggregation,
    open_editable_aggregation_table,
    recalculate_aggregation_defaults,
    recalculate_aggregation_totals,
    reload_aggregation_history,
    update_aggregation_tables,
)
from fiscal_app.ui.conversion_helpers import export_conversion_excel, import_conversion_excel, load_conversion_table
from fiscal_app.ui.export_helpers import (
    dataset_for_export,
    export_docx,
    export_excel,
    export_txt_html,
    filters_text,
    save_dialog,
)
from fiscal_app.ui.file_navigation_helpers import (
    load_current_file,
    on_file_activated,
    refresh_file_tree,
    reload_table,
    refresh_filter_list_widget,
    update_context_label,
    update_page_label,
)
from fiscal_app.ui.filter_helpers import (
    add_filter_from_form,
    apply_quick_filters,
    choose_columns,
    clear_filters,
    next_page,
    prev_page,
    remove_selected_filter,
)
from fiscal_app.ui.sql_helpers import (
    clear_param_form,
    collect_param_values,
    execute_sql_query,
    export_sql_results,
    filter_sql_results,
    on_query_failed,
    on_query_finished,
    on_sql_selected,
    populate_sql_combo,
    rebuild_param_form,
    show_sql_result_page,
    sql_next_page,
    sql_prev_page,
)
from fiscal_app.ui.traceability_helpers import (
    apply_traceability_filter,
    clear_traceability_filter,
    clear_traceability_state,
    open_traceability_file,
    traceability_files,
)


class PipelineWorker(QThread):
    finished_ok = Signal(object)
    failed = Signal(str)
    progress = Signal(str)

    def __init__(self, service: ServicoPipelineCompleto, cnpj: str, consultas: list[Path], tabelas: list[str], data_limite: str | None = None) -> None:
        super().__init__()
        self.service = service
        self.cnpj = cnpj
        self.consultas = consultas
        self.tabelas = tabelas
        self.data_limite = data_limite

    def run(self) -> None:
        try:
            result = self.service.executar_completo(self.cnpj, self.consultas, self.tabelas, self.data_limite, progresso=self.progress.emit)
        except Exception as exc:
            self.failed.emit(str(exc))
            return
        if result.ok:
            self.finished_ok.emit(result)
        else:
            message = "\n".join(result.erros) if result.erros else "Falha no pipeline oficial."
            self.failed.emit(message or "Falha sem detalhes.")


@dataclass
class ViewState:
    current_cnpj: str | None = None
    current_file: Path | None = None
    current_page: int = 1
    page_size: int = DEFAULT_PAGE_SIZE
    all_columns: list[str] | None = None
    visible_columns: list[str] | None = None
    filters: list[FilterCondition] | None = None
    total_rows: int = 0


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1560, 920)

        self.registry_service = RegistryService()
        self.parquet_service = ParquetService(root=CNPJ_ROOT)
        self.servico_pipeline_funcoes = ServicoPipelineCompleto()
        self.export_service = ExportService()
        self.servico_agregacao = ServicoAgregacao()
        self.sql_service = SqlService()

        self.state = ViewState(filters=[])
        self.current_page_df_all = pl.DataFrame()
        self.current_page_df_visible = pl.DataFrame()
        self._trace_df = pl.DataFrame()
        self.table_model = PolarsTableModel()
        self.aggregation_table_model = PolarsTableModel(checkable=True)
        self.results_table_model = PolarsTableModel(checkable=True)
        self.conversion_model = PolarsTableModel()
        self.trace_model = PolarsTableModel()
        self.sql_result_model = PolarsTableModel()
        self.pipeline_worker: PipelineWorker | None = None
        self.query_worker: QueryWorker | None = None
        self._sql_files: list = []
        self._sql_param_widgets: dict[str, QWidget] = {}
        self._sql_current_sql: str = ""
        self._sql_result_df: pl.DataFrame = pl.DataFrame()

        self._build_ui()
        self._connect_signals()
        self.refresh_cnpjs()
        self.refresh_logs()
        self._populate_sql_combo()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)

        splitter = QSplitter(Qt.Horizontal)
        root_layout.addWidget(splitter)

        splitter.addWidget(self._build_left_panel())
        splitter.addWidget(self._build_right_panel())
        splitter.setSizes([310, 1200])

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Pronto.")

    def _build_left_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)

        cnpj_box = QGroupBox("CNPJs")
        cnpj_layout = QVBoxLayout(cnpj_box)
        input_line = QHBoxLayout()
        self.cnpj_input = QLineEdit()
        self.cnpj_input.setPlaceholderText("Digite o CNPJ com ou sem máscara")
        self.btn_run_pipeline = QPushButton("Analisar CNPJ")
        input_line.addWidget(self.cnpj_input)
        input_line.addWidget(self.btn_run_pipeline)
        cnpj_layout.addLayout(input_line)

        date_line = QHBoxLayout()
        date_line.addWidget(QLabel("Data limite EFD:"))
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setDisplayFormat("dd/MM/yyyy")
        date_line.addWidget(self.date_input)
        cnpj_layout.addLayout(date_line)

        actions = QHBoxLayout()
        self.btn_refresh_cnpjs = QPushButton("Atualizar lista")
        self.btn_open_cnpj_folder = QPushButton("Abrir pasta")
        actions.addWidget(self.btn_refresh_cnpjs)
        actions.addWidget(self.btn_open_cnpj_folder)
        cnpj_layout.addLayout(actions)

        self.cnpj_list = QListWidget()
        cnpj_layout.addWidget(self.cnpj_list)
        layout.addWidget(cnpj_box)

        files_box = QGroupBox("Arquivos Parquet do CNPJ")
        files_layout = QVBoxLayout(files_box)
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels(["Arquivo", "Local"])
        files_layout.addWidget(self.file_tree)
        layout.addWidget(files_box)

        notes = QLabel(
            "Fluxo recomendado: execute as consultas SQL e gere o fluxo oficial de produtos "
            "(produtos_unidades → produtos → produtos_agrupados/produtos_final → fatores_conversao). "
            "Use a aba Rastreabilidade para auditar a origem das linhas, o vínculo com chave_produto/id_agrupado "
            "e os cálculos dos fatores."
        )
        notes.setWordWrap(True)
        layout.addWidget(notes)
        return panel

    def _build_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)

        header = QHBoxLayout()
        self.lbl_context = QLabel("Nenhum arquivo selecionado")
        self.lbl_context.setWordWrap(True)
        header.addWidget(self.lbl_context)
        header.addStretch()
        layout.addLayout(header)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_tab_consulta(), "Consulta")
        self.tabs.addTab(self._build_tab_sql_query(), "Consulta SQL")
        self.tabs.addTab(self._build_tab_agregacao(), "Agregação")
        self.tabs.addTab(self._build_tab_conversao(), "Fatores de Conversão")
        self.tabs.addTab(self._build_tab_rastreabilidade(), "Rastreabilidade")
        self.tabs.addTab(self._build_tab_logs(), "Logs")
        layout.addWidget(self.tabs)
        return panel

    def _build_tab_consulta(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        filter_box = QGroupBox("Filtros")
        filter_layout = QVBoxLayout(filter_box)
        form = QHBoxLayout()
        self.filter_column = QComboBox()
        self.filter_operator = QComboBox()
        self.filter_operator.addItems(["contém", "igual", "começa com", "termina com", ">", ">=", "<", "<=", "é nulo", "não é nulo"])
        self.filter_value = QLineEdit()
        self.filter_value.setPlaceholderText("Valor do filtro")
        self.btn_add_filter = QPushButton("Adicionar filtro")
        self.btn_clear_filters = QPushButton("Limpar filtros")
        form.addWidget(QLabel("Coluna"))
        form.addWidget(self.filter_column)
        form.addWidget(QLabel("Operador"))
        form.addWidget(self.filter_operator)
        form.addWidget(QLabel("Valor"))
        form.addWidget(self.filter_value)
        form.addWidget(self.btn_add_filter)
        form.addWidget(self.btn_clear_filters)
        filter_layout.addLayout(form)

        self.filter_list = QListWidget()
        self.filter_list.setMaximumHeight(90)
        filter_layout.addWidget(self.filter_list)

        filter_actions = QHBoxLayout()
        self.btn_remove_filter = QPushButton("Remover filtro selecionado")
        self.btn_choose_columns = QPushButton("Selecionar colunas")
        self.btn_prev_page = QPushButton("Página anterior")
        self.btn_next_page = QPushButton("Próxima página")
        self.lbl_page = QLabel("Página 0/0")
        filter_actions.addWidget(self.btn_remove_filter)
        filter_actions.addWidget(self.btn_choose_columns)
        filter_actions.addStretch()
        filter_actions.addWidget(self.btn_prev_page)
        filter_actions.addWidget(self.lbl_page)
        filter_actions.addWidget(self.btn_next_page)
        filter_layout.addLayout(filter_actions)
        layout.addWidget(filter_box)

        export_box = QGroupBox("Exportação")
        export_layout = QHBoxLayout(export_box)
        self.btn_export_excel_full = QPushButton("Excel - tabela completa")
        self.btn_export_excel_filtered = QPushButton("Excel - tabela filtrada")
        self.btn_export_excel_visible = QPushButton("Excel - colunas visíveis")
        self.btn_export_docx = QPushButton("Relatório Word")
        self.btn_export_html_txt = QPushButton("TXT com HTML")
        for btn in [self.btn_export_excel_full, self.btn_export_excel_filtered, self.btn_export_excel_visible, self.btn_export_docx, self.btn_export_html_txt]:
            export_layout.addWidget(btn)
        layout.addWidget(export_box)

        quick_filter_layout = QHBoxLayout()
        self.qf_norm = QLineEdit(); self.qf_norm.setPlaceholderText("Filtrar Desc. Norm")
        self.qf_desc = QLineEdit(); self.qf_desc.setPlaceholderText("Filtrar Descrição")
        self.qf_ncm = QLineEdit(); self.qf_ncm.setPlaceholderText("Filtrar NCM")
        self.qf_cest = QLineEdit(); self.qf_cest.setPlaceholderText("Filtrar CEST")
        for w in [self.qf_norm, self.qf_desc, self.qf_ncm, self.qf_cest]:
            w.setMaximumWidth(200)
            quick_filter_layout.addWidget(w)
        quick_filter_layout.addStretch()
        layout.addLayout(quick_filter_layout)

        self.table_view = QTableView()
        self.table_view.setModel(self.table_model)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSortingEnabled(False)
        self.table_view.setWordWrap(True)
        self.table_view.verticalHeader().setDefaultSectionSize(60)
        self.table_view.horizontalHeader().setMinimumSectionSize(40)
        self.table_view.horizontalHeader().setDefaultSectionSize(200)
        self.table_view.horizontalHeader().setMaximumSectionSize(300)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.setStyleSheet("QTableView::item { padding: 4px 2px; }")
        layout.addWidget(self.table_view, 1)
        return tab

    def _build_tab_agregacao(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        top_box = QGroupBox("Tabela Editável (Selecione linhas para agregar)")
        top_layout = QVBoxLayout(top_box)

        toolbar = QHBoxLayout()
        self.btn_open_editable_table = QPushButton("Abrir tabela editável do agrupamento")
        self.btn_execute_aggregation = QPushButton("Agregar Descrições (da seleção)")
        self.btn_recalc_defaults = QPushButton("♻️  Recalcular Padrões (Geral)")
        self.btn_recalc_totals = QPushButton("💰  Recalcular Totais")
        self.btn_open_group_trace = QPushButton("Abrir rastro do agrupamento")
        self.btn_open_group_sources = QPushButton("Abrir origens do agrupamento")
        for btn in [self.btn_open_editable_table, self.btn_execute_aggregation, self.btn_recalc_defaults, self.btn_recalc_totals, self.btn_open_group_trace, self.btn_open_group_sources]:
            toolbar.addWidget(btn)
        toolbar.addStretch()
        top_layout.addLayout(toolbar)

        agg_qf_layout = QHBoxLayout()
        self.aqf_norm = QLineEdit(); self.aqf_norm.setPlaceholderText("Filtrar Desc. Norm")
        self.aqf_desc = QLineEdit(); self.aqf_desc.setPlaceholderText("Filtrar Descrição")
        self.aqf_ncm = QLineEdit(); self.aqf_ncm.setPlaceholderText("Filtrar NCM")
        self.aqf_cest = QLineEdit(); self.aqf_cest.setPlaceholderText("Filtrar CEST")
        for w in [self.aqf_norm, self.aqf_desc, self.aqf_ncm, self.aqf_cest]:
            w.setMaximumWidth(200)
            agg_qf_layout.addWidget(w)
        agg_qf_layout.addStretch()
        top_layout.addLayout(agg_qf_layout)

        self.aggregation_table_view = QTableView()
        self.aggregation_table_view.setModel(self.aggregation_table_model)
        self.aggregation_table_view.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.aggregation_table_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.aggregation_table_view.setAlternatingRowColors(True)
        self.aggregation_table_view.setWordWrap(True)
        self.aggregation_table_view.verticalHeader().setDefaultSectionSize(60)
        self.aggregation_table_view.horizontalHeader().setMinimumSectionSize(40)
        self.aggregation_table_view.horizontalHeader().setDefaultSectionSize(200)
        self.aggregation_table_view.horizontalHeader().setMaximumSectionSize(300)
        self.aggregation_table_view.setStyleSheet("QTableView::item { padding: 4px 2px; }")
        top_layout.addWidget(self.aggregation_table_view, 1)
        layout.addWidget(top_box, 3)

        bottom_box = QGroupBox("Resultados da Sessão (Histórico)")
        bottom_layout = QVBoxLayout(bottom_box)
        self.results_table_view = QTableView()
        self.results_table_view.setModel(self.results_table_model)
        self.results_table_view.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.results_table_view.setAlternatingRowColors(True)
        self.results_table_view.setWordWrap(True)
        self.results_table_view.verticalHeader().setDefaultSectionSize(60)
        self.results_table_view.horizontalHeader().setMinimumSectionSize(40)
        self.results_table_view.horizontalHeader().setDefaultSectionSize(200)
        self.results_table_view.horizontalHeader().setMaximumSectionSize(300)
        self.results_table_view.setStyleSheet("QTableView::item { padding: 4px 2px; }")
        bottom_layout.addWidget(self.results_table_view, 1)
        layout.addWidget(bottom_box, 1)
        return tab

    def _build_tab_sql_query(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("SQL:"))
        self.sql_combo = QComboBox(); self.sql_combo.setMinimumWidth(300)
        top_bar.addWidget(self.sql_combo, 1)
        self.btn_sql_execute = QPushButton("▶  Executar Consulta")
        self.btn_sql_execute.setStyleSheet("QPushButton { font-weight: bold; padding: 6px 16px; }")
        self.btn_sql_export = QPushButton("Exportar Excel")
        top_bar.addWidget(self.btn_sql_execute)
        top_bar.addWidget(self.btn_sql_export)
        layout.addLayout(top_bar)

        splitter = QSplitter(Qt.Vertical)
        upper_widget = QWidget(); upper_layout = QHBoxLayout(upper_widget); upper_layout.setContentsMargins(0,0,0,0)
        sql_group = QGroupBox("Texto SQL"); sql_group_layout = QVBoxLayout(sql_group)
        self.sql_text_view = QPlainTextEdit(); self.sql_text_view.setReadOnly(True)
        self.sql_text_view.setStyleSheet("QPlainTextEdit { font-family: 'Consolas', 'Courier New', monospace; font-size: 12px; background: #1e1e2e; color: #cdd6f4; border: 1px solid #45475a; border-radius: 4px; padding: 8px; }")
        self.sql_text_view.setMinimumHeight(120)
        sql_group_layout.addWidget(self.sql_text_view)
        upper_layout.addWidget(sql_group, 3)
        param_group = QGroupBox("Parâmetros"); param_outer_layout = QVBoxLayout(param_group)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        self.sql_param_container = QWidget(); self.sql_param_form = QFormLayout(self.sql_param_container)
        self.sql_param_form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        scroll.setWidget(self.sql_param_container)
        param_outer_layout.addWidget(scroll)
        upper_layout.addWidget(param_group, 1)
        splitter.addWidget(upper_widget)

        result_widget = QWidget(); result_layout = QVBoxLayout(result_widget); result_layout.setContentsMargins(0,0,0,0)
        self.sql_status_label = QLabel("Selecione um SQL e clique em Executar.")
        self.sql_status_label.setStyleSheet("QLabel { padding: 4px 8px; background: #f0f4ff; border-radius: 4px; border: 1px solid #d0d8e8; color: #334155; font-weight: bold; }")
        result_layout.addWidget(self.sql_status_label)
        sql_filter_bar = QHBoxLayout()
        self.sql_result_search = QLineEdit(); self.sql_result_search.setPlaceholderText("Buscar nos resultados...")
        sql_filter_bar.addWidget(self.sql_result_search)
        self.sql_result_page_label = QLabel("")
        self.btn_sql_prev = QPushButton("◀ Anterior")
        self.btn_sql_next = QPushButton("Próxima ▶")
        sql_filter_bar.addWidget(self.btn_sql_prev); sql_filter_bar.addWidget(self.sql_result_page_label); sql_filter_bar.addWidget(self.btn_sql_next)
        result_layout.addLayout(sql_filter_bar)
        self.sql_result_table = QTableView(); self.sql_result_table.setModel(self.sql_result_model)
        self.sql_result_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.sql_result_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.sql_result_table.setAlternatingRowColors(True)
        self.sql_result_table.setSortingEnabled(False)
        self.sql_result_table.setWordWrap(True)
        self.sql_result_table.verticalHeader().setDefaultSectionSize(60)
        self.sql_result_table.horizontalHeader().setMinimumSectionSize(40)
        self.sql_result_table.horizontalHeader().setDefaultSectionSize(200)
        self.sql_result_table.horizontalHeader().setMaximumSectionSize(400)
        self.sql_result_table.horizontalHeader().setStretchLastSection(True)
        self.sql_result_table.setStyleSheet("QTableView::item { padding: 4px 2px; }")
        result_layout.addWidget(self.sql_result_table, 1)
        splitter.addWidget(result_widget)
        splitter.setSizes([280, 500])
        layout.addWidget(splitter, 1)
        return tab

    def _build_tab_conversao(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        info = QLabel(
            "Esta aba exibe a tabela fatores_conversao do fluxo oficial. Você pode exportar a base atual, "
            "importar revisões manuais e abrir os arquivos de auditoria e preços médios usados no cálculo."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        toolbar = QHBoxLayout()
        self.btn_refresh_conversao = QPushButton("Recarregar fatores")
        self.btn_refresh_conversao.setIcon(QApplication.style().standardIcon(QApplication.style().StandardPixmap.SP_BrowserReload))
        self.btn_export_conversao = QPushButton("Exportar revisão Excel")
        self.btn_import_conversao = QPushButton("Importar revisão Excel")
        self.btn_open_conv_audit = QPushButton("Abrir auditoria")
        self.btn_open_conv_prices = QPushButton("Abrir preços médios")
        for btn in [self.btn_refresh_conversao, self.btn_export_conversao, self.btn_import_conversao, self.btn_open_conv_audit, self.btn_open_conv_prices]:
            toolbar.addWidget(btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.conversion_table = QTableView()
        self.conversion_table.setModel(self.conversion_model)
        self.conversion_table.setAlternatingRowColors(True)
        self.conversion_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.conversion_table.setSortingEnabled(True)
        layout.addWidget(self.conversion_table)
        return tab

    def _build_tab_rastreabilidade(self) -> QWidget:
        self.trace_tab = QWidget()
        layout = QVBoxLayout(self.trace_tab)
        info = QLabel(
            "Abra aqui os arquivos de rastreabilidade do fluxo novo: origens brutas, mapa linha→produto, "
            "rastro produto→agrupamento, origens do agrupamento final e auditoria dos fatores."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        top = QHBoxLayout()
        self.btn_trace_origens = QPushButton("Origens brutas")
        self.btn_trace_produtos = QPushButton("Mapa produto")
        self.btn_trace_rastro = QPushButton("Rastro agrupamento")
        self.btn_trace_final = QPushButton("Origens agrupamento final")
        self.btn_trace_fatores = QPushButton("Auditoria fatores")
        for btn in [self.btn_trace_origens, self.btn_trace_produtos, self.btn_trace_rastro, self.btn_trace_final, self.btn_trace_fatores]:
            top.addWidget(btn)
        top.addStretch()
        layout.addLayout(top)

        filtros = QHBoxLayout()
        self.trace_filter_id_agrupado = QLineEdit(); self.trace_filter_id_agrupado.setPlaceholderText("Filtrar id_agrupado")
        self.trace_filter_chave_produto = QLineEdit(); self.trace_filter_chave_produto.setPlaceholderText("Filtrar chave_produto")
        self.btn_trace_apply = QPushButton("Aplicar filtro")
        self.btn_trace_clear = QPushButton("Limpar filtro")
        for w in [self.trace_filter_id_agrupado, self.trace_filter_chave_produto, self.btn_trace_apply, self.btn_trace_clear]:
            filtros.addWidget(w)
        filtros.addStretch()
        layout.addLayout(filtros)

        self.trace_status_label = QLabel("Nenhum arquivo de rastreabilidade carregado.")
        layout.addWidget(self.trace_status_label)

        self.trace_table = QTableView()
        self.trace_table.setModel(self.trace_model)
        self.trace_table.setAlternatingRowColors(True)
        self.trace_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.trace_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.trace_table.setWordWrap(True)
        self.trace_table.verticalHeader().setDefaultSectionSize(60)
        self.trace_table.horizontalHeader().setDefaultSectionSize(180)
        self.trace_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.trace_table, 1)
        return self.trace_tab

    def _build_tab_logs(self) -> QWidget:
        tab = QWidget(); layout = QVBoxLayout(tab)
        self.log_view = QPlainTextEdit(); self.log_view.setReadOnly(True)
        layout.addWidget(self.log_view)
        return tab

    def _connect_signals(self) -> None:
        self.btn_refresh_cnpjs.clicked.connect(self.refresh_cnpjs)
        self.btn_run_pipeline.clicked.connect(self.run_pipeline_for_input)
        self.cnpj_list.itemSelectionChanged.connect(self.on_cnpj_selected)
        self.file_tree.itemClicked.connect(self.on_file_activated)
        self.file_tree.itemDoubleClicked.connect(self.on_file_activated)
        self.btn_open_cnpj_folder.clicked.connect(self.open_cnpj_folder)

        self.btn_add_filter.clicked.connect(self.add_filter_from_form)
        self.btn_clear_filters.clicked.connect(self.clear_filters)
        self.btn_remove_filter.clicked.connect(self.remove_selected_filter)
        self.btn_choose_columns.clicked.connect(self.choose_columns)
        self.btn_prev_page.clicked.connect(self.prev_page)
        self.btn_next_page.clicked.connect(self.next_page)

        self.btn_export_excel_full.clicked.connect(lambda: self.export_excel("full"))
        self.btn_export_excel_filtered.clicked.connect(lambda: self.export_excel("filtered"))
        self.btn_export_excel_visible.clicked.connect(lambda: self.export_excel("visible"))
        self.btn_export_docx.clicked.connect(self.export_docx)
        self.btn_export_html_txt.clicked.connect(self.export_txt_html)

        self.btn_open_editable_table.clicked.connect(self.open_editable_aggregation_table)
        self.btn_execute_aggregation.clicked.connect(self.execute_aggregation)
        self.btn_recalc_defaults.clicked.connect(self.recalcular_padroes_agregacao)
        self.btn_recalc_totals.clicked.connect(self.recalcular_totais_agregacao)
        self.btn_open_group_trace.clicked.connect(self.abrir_rastro_agrupamento)
        self.btn_open_group_sources.clicked.connect(self.abrir_origens_agrupamento)

        for qf in [self.qf_norm, self.qf_desc, self.qf_ncm, self.qf_cest, self.aqf_norm, self.aqf_desc, self.aqf_ncm, self.aqf_cest]:
            qf.returnPressed.connect(self.apply_quick_filters)

        self.sql_combo.currentIndexChanged.connect(self._on_sql_selected)
        self.btn_sql_execute.clicked.connect(self._execute_sql_query)
        self.btn_sql_export.clicked.connect(self._export_sql_results)
        self.sql_result_search.returnPressed.connect(self._filter_sql_results)
        self.btn_sql_prev.clicked.connect(self._sql_prev_page)
        self.btn_sql_next.clicked.connect(self._sql_next_page)

        self.btn_refresh_conversao.clicked.connect(self.atualizar_aba_conversao)
        self.btn_export_conversao.clicked.connect(self.exportar_conversao_excel)
        self.btn_import_conversao.clicked.connect(self.importar_conversao_excel)
        self.btn_open_conv_audit.clicked.connect(self.abrir_auditoria_fatores)
        self.btn_open_conv_prices.clicked.connect(self.abrir_precos_fatores)

        self.btn_trace_origens.clicked.connect(self.abrir_origens_brutas)
        self.btn_trace_produtos.clicked.connect(self.abrir_mapa_produtos)
        self.btn_trace_rastro.clicked.connect(self.abrir_rastro_agrupamento)
        self.btn_trace_final.clicked.connect(self.abrir_origens_agrupamento)
        self.btn_trace_fatores.clicked.connect(self.abrir_auditoria_fatores)
        self.btn_trace_apply.clicked.connect(self.aplicar_filtro_rastreabilidade)
        self.btn_trace_clear.clicked.connect(self.limpar_filtro_rastreabilidade)

    def show_error(self, title: str, message: str) -> None:
        QMessageBox.critical(self, title, message)

    def show_info(self, title: str, message: str) -> None:
        QMessageBox.information(self, title, message)

    def refresh_cnpjs(self) -> None:
        known = {record.cnpj for record in self.registry_service.list_records()}
        known.update(self.parquet_service.list_cnpjs())
        current = self.state.current_cnpj
        self.cnpj_list.clear()
        for cnpj in sorted(known):
            self.cnpj_list.addItem(cnpj)
        if current:
            matches = self.cnpj_list.findItems(current, Qt.MatchExactly)
            if matches:
                self.cnpj_list.setCurrentItem(matches[0])

    def run_pipeline_for_input(self) -> None:
        try:
            cnpj = self.servico_pipeline_funcoes.servico_extracao.sanitizar_cnpj(self.cnpj_input.text())
        except Exception as exc:
            self.show_error("CNPJ inválido", str(exc)); return
        consultas_disp = self.servico_pipeline_funcoes.servico_extracao.listar_consultas()
        if not consultas_disp:
            self.show_error("Sem consultas", "Nenhum arquivo .sql encontrado em c:\\funcoes\\consultas_fonte"); return
        dlg_sql = DialogoSelecaoConsultas(consultas_disp, self)
        if not dlg_sql.exec(): return
        sql_selecionados = dlg_sql.consultas_selecionadas()
        tabelas_disp = self.servico_pipeline_funcoes.servico_tabelas.listar_tabelas()
        dlg_tab = DialogoSelecaoTabelas(tabelas_disp, self)
        if not dlg_tab.exec(): return
        tabelas_selecionadas = dlg_tab.tabelas_selecionadas()
        if not sql_selecionados and not tabelas_selecionadas: return
        self.btn_run_pipeline.setEnabled(False)
        self.status.showMessage(f"Executando pipeline oficial para {cnpj}...")
        data_limite = self.date_input.date().toString("dd/MM/yyyy")
        self.pipeline_worker = PipelineWorker(self.servico_pipeline_funcoes, cnpj, sql_selecionados, tabelas_selecionadas, data_limite)
        self.pipeline_worker.finished_ok.connect(self.on_pipeline_finished)
        self.pipeline_worker.failed.connect(self.on_pipeline_failed)
        self.pipeline_worker.progress.connect(self.status.showMessage)
        self.pipeline_worker.start()

    def on_pipeline_finished(self, result: ResultadoPipeline) -> None:
        self.btn_run_pipeline.setEnabled(True)
        self.registry_service.upsert(result.cnpj, ran_now=True)
        self.status.showMessage(f"Pipeline oficial concluído para {result.cnpj}.")
        self.refresh_cnpjs()
        matches = self.cnpj_list.findItems(result.cnpj, Qt.MatchExactly)
        if matches:
            self.cnpj_list.setCurrentItem(matches[0])
            self.refresh_file_tree(result.cnpj)
            self.atualizar_aba_conversao()
        tabelas_fluxo = [item for item in result.arquivos_gerados if item in {"produtos_unidades", "produtos", "produtos_agrupados", "produtos_final", "fatores_conversao"}]
        msg = "\n".join(result.mensagens[-10:]) if result.mensagens else "Processado com sucesso."
        self.show_info("Pipeline oficial concluído", f"CNPJ {result.cnpj} processado.\n\nFluxo de produtos: {', '.join(tabelas_fluxo) if tabelas_fluxo else 'sem etapas registradas'}\n\nÚltimas mensagens:\n{msg}")

    def on_pipeline_failed(self, message: str) -> None:
        self.btn_run_pipeline.setEnabled(True)
        self.status.showMessage("Falha na execução do pipeline oficial.")
        self.show_error("Falha no pipeline oficial", message)

    def on_cnpj_selected(self) -> None:
        item = self.cnpj_list.currentItem()
        if item is None: return
        cnpj = item.text(); self.state.current_cnpj = cnpj
        self.registry_service.upsert(cnpj, ran_now=False)
        self.refresh_file_tree(cnpj)
        self.atualizar_aba_conversao()
        self.recarregar_historico_agregacao(cnpj)
        self.limpar_rastreabilidade()

    def refresh_file_tree(self, cnpj: str) -> None:
        refresh_file_tree(self, cnpj)

    def on_file_activated(self, item, column: int) -> None:
        on_file_activated(self, item, column)

    def load_current_file(self, reset_columns: bool = False) -> None:
        load_current_file(self, reset_columns)

    def reload_table(self, update_main_view: bool = True) -> None:
        reload_table(self, update_main_view)

    def _update_page_label(self) -> None:
        update_page_label(self)

    def _update_context_label(self) -> None:
        update_context_label(self)

    def add_filter_from_form(self) -> None:
        add_filter_from_form(self)

    def clear_filters(self) -> None:
        clear_filters(self)

    def remove_selected_filter(self) -> None:
        remove_selected_filter(self)

    def _refresh_filter_list_widget(self) -> None:
        refresh_filter_list_widget(self)

    def choose_columns(self) -> None:
        choose_columns(self)

    def prev_page(self) -> None:
        prev_page(self)

    def next_page(self) -> None:
        next_page(self)

    def _save_dialog(self, title: str, pattern: str) -> Path | None:
        return save_dialog(self, title, pattern)

    def _filters_text(self) -> str:
        return filters_text(self)

    def _dataset_for_export(self, mode: str) -> pl.DataFrame:
        return dataset_for_export(self, mode)

    def export_excel(self, mode: str) -> None:
        export_excel(self, mode)

    def export_docx(self) -> None:
        export_docx(self)

    def export_txt_html(self) -> None:
        export_txt_html(self)

    def open_editable_aggregation_table(self) -> None:
        open_editable_aggregation_table(self)

    def execute_aggregation(self) -> None:
        execute_aggregation(self)

    def apply_quick_filters(self) -> None:
        apply_quick_filters(self)

    def refresh_logs(self) -> None:
        import json
        logs = [json.dumps(log) for log in self.servico_agregacao.ler_linhas_log()]
        self.log_view.setPlainText("\n".join(logs))

    def open_cnpj_folder(self) -> None:
        if not self.state.current_cnpj:
            self.show_error("CNPJ não selecionado", "Selecione um CNPJ para abrir a pasta."); return
        target = self.parquet_service.cnpj_dir(self.state.current_cnpj)
        if not target.exists():
            self.show_error("Pasta inexistente", f"A pasta {target} ainda não foi criada."); return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(target)))

    def atualizar_aba_conversao(self) -> None:
        load_conversion_table(self)

    def exportar_conversao_excel(self) -> None:
        export_conversion_excel(self)

    def importar_conversao_excel(self) -> None:
        import_conversion_excel(self)

    def recalcular_padroes_agregacao(self) -> None:
        recalculate_aggregation_defaults(self)

    def recalcular_totais_agregacao(self) -> None:
        recalculate_aggregation_totals(self)

    def recarregar_historico_agregacao(self, cnpj: str) -> None:
        reload_aggregation_history(self, cnpj)

    def atualizar_tabelas_agregacao(self) -> None:
        update_aggregation_tables(self)

    def _arquivos_rastreabilidade(self) -> dict[str, Path]:
        return traceability_files(self.state.current_cnpj)

    def limpar_rastreabilidade(self) -> None:
        clear_traceability_state(self)

    def _abrir_arquivo_rastreabilidade(self, path: Path, titulo: str) -> None:
        open_traceability_file(self, path, titulo)

    def aplicar_filtro_rastreabilidade(self) -> None:
        apply_traceability_filter(self)

    def limpar_filtro_rastreabilidade(self) -> None:
        clear_traceability_filter(self)

    def abrir_origens_brutas(self) -> None:
        self._abrir_arquivo_rastreabilidade(self._arquivos_rastreabilidade()["origens_brutas"], "Origens brutas")

    def abrir_mapa_produtos(self) -> None:
        self._abrir_arquivo_rastreabilidade(self._arquivos_rastreabilidade()["mapa_produtos"], "Mapa origem → produto")

    def abrir_rastro_agrupamento(self) -> None:
        self._abrir_arquivo_rastreabilidade(self._arquivos_rastreabilidade()["rastro_agrupamento"], "Rastro produto → agrupamento")

    def abrir_origens_agrupamento(self) -> None:
        self._abrir_arquivo_rastreabilidade(self._arquivos_rastreabilidade()["origens_agrupamento"], "Origens do agrupamento final")

    def abrir_auditoria_fatores(self) -> None:
        self._abrir_arquivo_rastreabilidade(self._arquivos_rastreabilidade()["auditoria_fatores"], "Auditoria dos fatores")

    def abrir_precos_fatores(self) -> None:
        self._abrir_arquivo_rastreabilidade(self._arquivos_rastreabilidade()["precos_fatores"], "Preços médios dos fatores")

    _sql_result_page: int = 1
    _sql_result_page_size: int = DEFAULT_PAGE_SIZE

    def _populate_sql_combo(self) -> None:
        populate_sql_combo(self)

    def _on_sql_selected(self, index: int) -> None:
        on_sql_selected(self, index)

    def _clear_param_form(self) -> None:
        clear_param_form(self)

    def _rebuild_param_form(self, params) -> None:
        rebuild_param_form(self, params)

    def _collect_param_values(self) -> dict[str, str]:
        return collect_param_values(self)

    def _execute_sql_query(self) -> None:
        execute_sql_query(self)

    def _on_query_finished(self, df: pl.DataFrame) -> None:
        on_query_finished(self, df)

    def _on_query_failed(self, message: str) -> None:
        on_query_failed(self, message)

    def _show_sql_result_page(self) -> None:
        show_sql_result_page(self)

    def _sql_prev_page(self) -> None:
        sql_prev_page(self)

    def _sql_next_page(self) -> None:
        sql_next_page(self)

    def _filter_sql_results(self) -> None:
        filter_sql_results(self)

    def _export_sql_results(self) -> None:
        export_sql_results(self)
