"""
Configurações do SEFIN Audit Tool.
Define diretórios e funções de auxílio para organização dos dados por CNPJ.
"""
from pathlib import Path
import os

# Diretório raiz do projeto
DIR_PROJETO = Path(__file__).resolve().parent

# Diretórios principais
DIR_SQL = DIR_PROJETO / "consultas_fonte"
DIR_CNPJS = DIR_PROJETO / "CNPJ"
DIR_REFERENCIAS = DIR_PROJETO / "referencias"

# Criar diretórios automaticamente
DIR_CNPJS.mkdir(parents=True, exist_ok=True)

# Consultas SQL disponíveis para extração
CONSULTAS_SQL = {
    arquivo.stem: arquivo for arquivo in sorted(DIR_SQL.glob("*.sql"))
}

# Parâmetros comuns das consultas (bind variables)
PARAMETROS_DESCRICAO = {
    "CNPJ": "CNPJ (apenas números)",
}


# ──────────────────────────────────────────────
# CNPJs dos Órgãos e Empresas Públicas do Estado de Rondônia
# ──────────────────────────────────────────────
CNPJS_ORGAOS_PUBLICOS_RO = [
    '00394585000171', '00854776000179', '01072076000195', '01131631000102', '01664910000131', '02328663000165', '02603612000102',
    '03092697000166', '03682401000167', '03693136000112', '04285920000154', '04287520000188', '04293700000172', '04381083000167',
    '04420980000132', '04562872000102', '04564530000113', '04696490000163', '04793055000157', '04794681000168', '04798328000156',
    '04801221000110', '05599253000147', '05888813000183', '05957049000150', '06188804000142', '07098779000179', '07172665000121',
    '07824639000130', '07864604000125', '08817403000130', '09235305000157', '09317468000189', '09601829000114', '10459011000198',
    '10466386000185', '10849442000160', '11379786000116', '12150848000186', '12443392000142', '15519525000105', '15837081000156',
    '15849540000111', '15883796000145', '17900001000195', '18677407000113', '19463485000188', '19630756000142', '19907343000162',
    '22069966000118', '22078441000149', '23058368000106', '23059866000173', '23087774000105', '23860287000125', '23866256000181',
    '23929840000139', '26766814000125', '29512110000114', '29557720000134', '29581876000150', '29887313000195', '30475010000144',
    '30809485000120', '30833275000177', '33500189000130', '34481028000100', '34985801000175', '36335745000159', '37621806000107',
    '39774456000144', '41175256000117', '41802908000104', '44590106000168', '50380522000134', '53270238000101', '55102530000132',
    '63752604000104', '84745017000168'
]


def obter_diretorios_cnpj(cnpj: str):
    """
    Retorna os caminhos para salvar arquivos parquet, análises e relatórios de um CNPJ.
    Cria os diretórios se não existirem.

    Estrutura:
        CNPJ / <cnpj> / arquivos_parquet
        CNPJ / <cnpj> / analises
        CNPJ / <cnpj> / relatorios

    Returns:
        tuple: (dir_parquet, dir_analises, dir_relatorios)
    """
    cnpj_limpo = "".join(filter(str.isdigit, str(cnpj)))

    if not cnpj_limpo:
        cnpj_limpo = "sem_cnpj"

    base_cnpj = DIR_CNPJS / cnpj_limpo
    dir_parquet = base_cnpj / "arquivos_parquet"
    dir_analises = base_cnpj / "analises"
    dir_relatorios = base_cnpj / "relatorios"

    for d in [dir_parquet, dir_analises, dir_relatorios]:
        d.mkdir(parents=True, exist_ok=True)

    return dir_parquet, dir_analises, dir_relatorios
