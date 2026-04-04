"""
Utilitários de interface gráfica.

Contém funções auxiliares para manipulação de tabelas,
atalhos de teclado e validações na UI.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QKeySequence, QShortcut

if TYPE_CHECKING:
    from PySide6.QtWidgets import QDateEdit, QTableView

# Atalhos de teclado padrão
ATALHOS_UI = {
    "Ctrl+F": "Focar busca na aba ativa",
    "Ctrl+Shift+F": "Selecionar colunas",
    "Ctrl+L": "Limpar filtros",
    "Ctrl+E": "Exportar Excel",
    "Ctrl+Shift+D": "Destacar tabela",
    "Ctrl+R": "Recarregar tabela",
    "Ctrl+Shift+K": "Fio de Ouro",
    "Ctrl+C": "Copiar seleção",
}

# Tooltips de colunas fiscais
TOOLTIPS_COLUNAS = {
    "id_agrupado": "Identificador único do produto agrupado",
    "fonte": "Origem: c170, nfe, nfce, bloco_h, gerado",
    "q_conv": "Quantidade convertida para unidade de referência",
    "saldo_estoque_anual": "Saldo físico acumulado no ano",
    "custo_medio_anual": "Custo médio móvel calculado",
    "entr_desac_anual": "Entradas desacobertadas (alerta: saída sem saldo)",
    "preco_item": "Preço unitário da operação",
    "unid_ref": "Unidade de referência do produto",
    "fator": "Fator de conversão entre unidades",
    "ncm_padrao": "Classificação NCM padronizada",
    "cest_padrao": "Classificação CEST padronizada",
    "co_sefin_final": "Código SEFIN final após agrupamento",
    "co_sefin_agr": "Códigos SEFIN agregados do grupo",
    "it_pc_interna": "Classificação tributária: interna",
    "it_in_st": "Classificação tributária: substituição",
    "it_pc_mva": "Classificação tributária: MVA",
    "it_in_mva_ajustado": "Classificação tributária: MVA ajustado",
    "it_pc_reducao": "Classificação tributária: redução",
    "it_in_reducao_credito": "Classificação tributária: redução crédito",
    "ano": "Ano civil de referência",
    "mes": "Mês de referência (1-12)",
    "valor_entradas": "Valor total das entradas no período",
    "valor_saidas": "Valor total das saídas no período",
    "saldo_mes": "Saldo físico no final do mês",
    "custo_medio_mes": "Custo médio do mês",
    "valor_estoque": "Valor financeiro do estoque",
    "descr_padrao": "Descrição padronizada do grupo",
    "lista_descricoes": "Todas as descrições originais do grupo",
    "lista_co_sefin": "Todos os códigos SEFIN do grupo",
    "co_sefin_padrao": "Código SEFIN mais frequente do grupo",
    "co_sefin_divergentes": "Indica se há múltiplos SEFIN no grupo",
    "fator": "Fator de conversão (editável)",
    "chave_acesso": "Chave de acesso da NF-e (44 dígitos)",
    "cnpj_emitente": "CNPJ do emitente da nota",
    "cfop": "Código Fiscal de Operações e Prestações",
    "cst": "Código de Situação Tributária",
}

COLUNAS_CHAVE = {"id_agrupado", "id_agregado", "descr_padrao", "descricao", "descricao_normalizada"}


def criar_atalho(parent, chave: str, callback) -> QShortcut:
    """Cria um atalho de teclado."""
    shortcut = QShortcut(QKeySequence(chave), parent)
    shortcut.activated.connect(callback)
    return shortcut


def configurar_atalhos_basicos(main_window) -> None:
    """Configura atalhos de teclado básicos na janela principal."""
    def _focar_busca():
        main_window._focar_busca_ativa()
    criar_atalho(main_window, "Ctrl+F", _focar_busca)

    def _limpar_filtros():
        main_window._limpar_filtros_ativos()
    criar_atalho(main_window, "Ctrl+L", _limpar_filtros)

    def _exportar_excel():
        main_window._exportar_excel_ativo()
    criar_atalho(main_window, "Ctrl+E", _exportar_excel)

    def _destacar_tabela():
        main_window._destacar_tabela_ativa()
    criar_atalho(main_window, "Ctrl+Shift+D", _destacar_tabela)

    def _recarregar():
        main_window._recarregar_tabela_ativa()
    criar_atalho(main_window, "Ctrl+R", _recarregar)

    def _fio_de_ouro():
        main_window._fio_de_ouro_selecionado()
    criar_atalho(main_window, "Ctrl+Shift+K", _fio_de_ouro)


def validar_intervalo_datas(data_ini: QDateEdit, data_fim: QDateEdit) -> bool:
    """Valida se data_ini <= data_fim. Se data_ini > data_fim, ajusta data_fim."""
    ini = data_ini.date()
    fim = data_fim.date()
    if ini.isNull() or fim.isNull():
        return True
    if ini > fim:
        data_fim.setDate(ini)
        return False
    return True


def conectar_validacao_datas(data_ini: QDateEdit, data_fim: QDateEdit) -> None:
    """Conecta validação automática entre dois QDateEdit."""
    def _on_ini_changed(_date):
        ini = data_ini.date()
        if not ini.isNull():
            data_fim.setMinimumDate(ini)
    def _on_fim_changed(_date):
        fim = data_fim.date()
        if not fim.isNull():
            data_ini.setMaximumDate(fim)
    data_ini.dateChanged.connect(_on_ini_changed)
    data_fim.dateChanged.connect(_on_fim_changed)


def resize_columns_with_sample(table: QTableView, max_sample: int = 200) -> None:
    """Redimensiona colunas usando amostragem para performance."""
    model = table.model()
    if model is None or model.rowCount() == 0:
        return
    table.resizeColumnsToContents()
    header = table.horizontalHeader()
    for col in range(model.columnCount()):
        current_width = header.sectionSize(col)
        max_allowed = 420
        min_allowed = 40
        if current_width > max_allowed:
            header.resizeSection(col, max_allowed)
        elif current_width < min_allowed:
            header.resizeSection(col, min_allowed)


def obter_tooltip_coluna(coluna: str) -> str | None:
    """Retorna tooltip para uma coluna baseado no nome."""
    if coluna is None:
        return None
    nome = coluna.strip().lower()
    return TOOLTIPS_COLUNAS.get(nome)


def aplicar_tooltips_tabela(table) -> None:
    """Aplica tooltips nas colunas de uma tabela."""
    model = table.model()
    if model is None:
        return
    df = model.dataframe
    if df.is_empty():
        return
    header = table.horizontalHeader()
    offset = 1 if getattr(model, 'checkable', False) else 0
    for col_idx, col_name in enumerate(df.columns):
        tooltip = obter_tooltip_coluna(col_name)
        if tooltip:
            header.model().setHeaderData(col_idx + offset, Qt.Horizontal, tooltip, Qt.ToolTipRole)


def fixar_colunas_chave(table, colunas_para_fixar: list[str] | None = None) -> None:
    """Reorganiza colunas para manter as mais importantes à esquerda."""
    model = table.model()
    if model is None:
        return
    df = model.dataframe
    if df.is_empty():
        return
    colunas_alvo = set(colunas_para_fixar or COLUNAS_CHAVE)
    colunas_atuais = list(df.columns)
    colunas_fixas = [c for c in colunas_alvo if c in colunas_atuais]
    if not colunas_fixas:
        return
    header = table.horizontalHeader()
    posicao_esperada = 0
    offset_checkbox = 1 if getattr(model, 'checkable', False) else 0
    for col_alvo in colunas_fixas:
        if col_alvo not in colunas_atuais:
            continue
        idx_atual = colunas_atuais.index(col_alvo)
        idx_visual = idx_atual + offset_checkbox
        pos_visual_esperada = posicao_esperada + offset_checkbox
        if idx_visual != pos_visual_esperada:
            header.moveSection(idx_visual, pos_visual_esperada)
            colunas_atuais.remove(col_alvo)
            colunas_atuais.insert(posicao_esperada, col_alvo)
        posicao_esperada += 1
