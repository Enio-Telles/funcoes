from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
import math
import re
import unicodedata
from typing import Any

STOPWORDS = {
    "A", "AS", "O", "OS", "DE", "DA", "DO", "DAS", "DOS", "COM", "PARA", "POR",
    "E", "EM", "NA", "NO", "NAS", "NOS", "UM", "UMA",
}

# Padrões de colunas para formatação contextual
COLUNAS_NCM = {"ncm", "ncm_padrao", "ncm_final"}
COLUNAS_CEST = {"cest", "cest_padrao", "cest_final"}
COLUNAS_GTIN = {"gtin", "gtin_padrao", "ean", "codigo_barras"}
COLUNAS_CNPJ = {"cnpj", "cnpj_emitente", "cnpj_destinatario"}


def remove_accents(text: str | None) -> str | None:
    if text is None:
        return None
    normalized = unicodedata.normalize("NFKD", str(text))
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def normalize_text(text: str | None) -> str:
    if text is None:
        return ""
    text = remove_accents(text) or ""
    text = text.upper()
    text = re.sub(r"[^A-Z0-9\s]", " ", text)
    tokens = [token for token in text.split() if token and token not in STOPWORDS]
    return " ".join(tokens)


def natural_sort_key(value: str | None) -> list[Any]:
    text = "" if value is None else str(value)
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", text)]


def _identificar_tipo_coluna(column_name: str | None) -> str | None:
    """Identifica o tipo de formatação baseado no nome da coluna."""
    if column_name is None:
        return None
    nome = column_name.strip().lower()
    for tipo, colunas in [
        ("ncm", COLUNAS_NCM),
        ("cest", COLUNAS_CEST),
        ("gtin", COLUNAS_GTIN),
        ("cnpj", COLUNAS_CNPJ),
    ]:
        if nome in colunas:
            return tipo
    for sufixo, tipo in [
        ("_ncm", "ncm"), ("ncm_", "ncm"),
        ("_cest", "cest"), ("cest_", "cest"),
        ("_gtin", "gtin"), ("gtin_", "gtin"),
        ("_cnpj", "cnpj"), ("cnpj_", "cnpj"),
    ]:
        if nome.endswith(sufixo) or nome.startswith(sufixo):
            return tipo
    return None


def _formatar_ncm(valor: str) -> str:
    """Formata NCM no padrão XX.XX.XX.XX (8 dígitos)."""
    digits = re.sub(r"\D", "", valor)
    if len(digits) == 8:
        return f"{digits[:2]}.{digits[2:4]}.{digits[4:6]}.{digits[6:]}"
    if len(digits) == 6:
        return f"{digits[:2]}.{digits[2:4]}.{digits[4:]}"
    return valor


def _formatar_cest(valor: str) -> str:
    """Formata CEST no padrão XX.XXX.XX (7 dígitos)."""
    digits = re.sub(r"\D", "", valor)
    if len(digits) == 7:
        return f"{digits[:2]}.{digits[2:5]}.{digits[5:]}"
    return valor


def _formatar_gtin(valor: str) -> str:
    """Formata GTIN com espaçamento para legibilidade."""
    digits = re.sub(r"\D", "", valor)
    if len(digits) == 13:
        return f"{digits[:3]} {digits[3:7]} {digits[7:12]} {digits[12]}"
    if len(digits) == 8:
        return f"{digits[:3]} {digits[3:7]} {digits[7:]}"
    return valor


def _formatar_cnpj(valor: str) -> str:
    """Formata CNPJ no padrão XX.XXX.XXX/XXXX-XX."""
    digits = re.sub(r"\D", "", valor)
    if len(digits) == 14:
        return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"
    return valor


def display_cell(value: Any, column_name: str | None = None) -> str:
    if value is None:
        return ""

    if hasattr(value, "to_list") and callable(getattr(value, "to_list")):
        try:
            value = value.to_list()
        except Exception:
            pass

    if isinstance(value, (list, tuple)):
        return ", ".join(display_cell(v, column_name) for v in value if v is not None)

    if isinstance(value, bool):
        return "true" if value else "false"

    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y %H:%M:%S")

    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")

    if isinstance(value, str):
        # Formatar tipos fiscais se identificados
        tipo = _identificar_tipo_coluna(column_name)
        if tipo == "ncm":
            return _formatar_ncm(value)
        if tipo == "cest":
            return _formatar_cest(value)
        if tipo == "gtin":
            return _formatar_gtin(value)
        if tipo == "cnpj":
            return _formatar_cnpj(value)

        # Tentar detectar datas ISO
        valor_data = _parse_data_iso(value)
        if valor_data is not None:
            if isinstance(valor_data, datetime):
                return valor_data.strftime("%d/%m/%Y %H:%M:%S")
            return valor_data.strftime("%d/%m/%Y")

        return value

    if isinstance(value, Decimal):
        if math.isnan(float(value)) or math.isinf(float(value)):
            return ""
        return _formatar_numero_br(value, 2)

    if isinstance(value, (int, float)):
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return ""
        if isinstance(value, int):
            return _formatar_numero_br(value, 0)
        return _formatar_numero_br(value, 2)

    return str(value)


def _parse_data_iso(texto: str) -> datetime | date | None:
    texto = texto.strip()
    if not texto:
        return None
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", texto):
        try:
            return datetime.strptime(texto, "%Y-%m-%d").date()
        except ValueError:
            return None
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2})?(\.\d{1,6})?", texto):
        normalizado = texto.replace("T", " ")
        for formato in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                return datetime.strptime(normalizado, formato)
            except ValueError:
                continue
    return None


def _formatar_numero_br(valor, casas_decimais: int) -> str:
    numero = float(valor)
    texto = f"{numero:,.{casas_decimais}f}"
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")
