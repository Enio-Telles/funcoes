"""
Utilitários visuais para a interface gráfica.

Contém resolvers de cor, fonte e formatação para customização
das tabelas na interface PySide6.
"""
from __future__ import annotations

from typing import Any

from PySide6.QtGui import QColor, QFont

# Cores padrão para indicadores visuais
COR_ALERTA_VERMELHO = QColor("#ef4444")
COR_ALERTA_AMARELO = QColor("#f59e0b")
COR_SUCESSO = QColor("#22c55e")
COR_INFO = QColor("#3b82f6")
COR_NEUTRO = QColor("#9ca3af")
COR_FUNDO_NULO = QColor("#f3f4f6")
COR_FUNDO_NULO_DARK = QColor("#374151")


def resolver_fundo_nulo(row_data: dict[str, Any], coluna: str) -> QColor | None:
    """Retorna cor de fundo suave para células com valores nulos ou vazios."""
    valor = row_data.get(coluna)
    if valor is None or valor == "" or valor == "":
        return COR_FUNDO_NULO
    return None


def mov_estoque_foreground(row_data: dict[str, Any], coluna: str) -> QColor | None:
    """
    Cor do texto para movimentação de estoque.
    - entr_desac_anual > 0 → vermelho (alerta fiscal)
    - Tipo_operacao com 'ENTRADA' → verde
    - Tipo_operacao com 'SAIDA' → vermelho suave
    - Tipo_operacao com 'ESTOQUE' → azul
    """
    if coluna == "entr_desac_anual":
        valor = row_data.get("entr_desac_anual", 0)
        try:
            if valor is not None and float(valor) > 0:
                return COR_ALERTA_VERMELHO
        except (ValueError, TypeError):
            pass
        return None

    if coluna == "saldo_estoque_anual":
        valor = row_data.get("saldo_estoque_anual")
        try:
            if valor is not None and float(valor) < 0:
                return COR_ALERTA_VERMELHO
        except (ValueError, TypeError):
            pass
        return None

    if coluna in ("q_conv", "preco_item", "preco_unit"):
        valor = row_data.get(coluna)
        if valor is None or valor == "":
            return COR_NEUTRO
        return None

    tipo_op = row_data.get("Tipo_operacao", "") or ""
    if isinstance(tipo_op, str):
        tipo_op_lower = tipo_op.lower()
        if "entrada" in tipo_op_lower:
            if coluna == "q_conv":
                return COR_SUCESSO
        elif "saida" in tipo_op_lower:
            if coluna == "q_conv":
                return QColor("#dc2626")
        elif "estoque" in tipo_op_lower:
            if coluna == "q_conv":
                return COR_INFO

    return None


def mov_estoque_background(row_data: dict[str, Any], coluna: str) -> QColor | None:
    """Fundo para movimentação de estoque."""
    if coluna == "entr_desac_anual":
        valor = row_data.get("entr_desac_anual", 0)
        try:
            if valor is not None and float(valor) > 0:
                return QColor("#fef3c7")
        except (ValueError, TypeError):
            pass
    return resolver_fundo_nulo(row_data, coluna)


def mov_estoque_font(row_data: dict[str, Any], coluna: str) -> QFont | None:
    """Fonte para movimentação de estoque."""
    if coluna == "entr_desac_anual":
        valor = row_data.get("entr_desac_anual", 0)
        try:
            if valor is not None and float(valor) > 0:
                font = QFont()
                font.setBold(True)
                return font
        except (ValueError, TypeError):
            pass

    tipo_op = row_data.get("Tipo_operacao", "") or ""
    if isinstance(tipo_op, str) and "estoque final" in tipo_op.lower():
        font = QFont()
        font.setItalic(True)
        return font
    return None


def aba_anual_foreground(row_data: dict[str, Any], coluna: str) -> QColor | None:
    """Destaque visual para tabela anual."""
    if coluna == "entr_desac_anual":
        valor = row_data.get("entr_desac_anual", 0)
        try:
            if valor is not None and float(valor) > 0:
                return COR_ALERTA_VERMELHO
        except (ValueError, TypeError):
            pass
    if coluna == "saldo_estoque_anual":
        valor = row_data.get("saldo_estoque_anual")
        try:
            if valor is not None and float(valor) < 0:
                return COR_ALERTA_VERMELHO
        except (ValueError, TypeError):
            pass
    return None


def aba_anual_background(row_data: dict[str, Any], coluna: str) -> QColor | None:
    """Fundo para tabela anual."""
    return resolver_fundo_nulo(row_data, coluna)


def aba_mensal_foreground(row_data: dict[str, Any], coluna: str) -> QColor | None:
    """Destaque visual para tabela mensal."""
    if coluna in ("saldo_estoque", "entr_desac"):
        valor = row_data.get(coluna)
        try:
            if valor is not None and float(valor) < 0:
                return COR_ALERTA_VERMELHO
        except (ValueError, TypeError):
            pass
    return None


def aba_mensal_background(row_data: dict[str, Any], coluna: str) -> QColor | None:
    """Fundo para tabela mensal."""
    return resolver_fundo_nulo(row_data, coluna)
