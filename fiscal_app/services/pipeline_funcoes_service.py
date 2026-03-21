"""
Serviço de pipeline que orquestra:
  1. Extração Oracle — executa SQLs selecionados de c:\\funcoes\\consultas_fonte
  2. Geração de tabelas — executa o pipeline oficial de produtos em
     c:\\funcoes\\funcoes_tabelas\\tabela_produtos
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import polars as pl

FUNCOES_DIR = Path(r"c:\funcoes")
AUXILIARES_DIR = FUNCOES_DIR / "funcoes_auxiliares"
TABELA_PRODUTOS_DIR = FUNCOES_DIR / "funcoes_tabelas" / "tabela_produtos"
CONSULTAS_FONTE_DIR = FUNCOES_DIR / "consultas_fonte"
CNPJ_ROOT = FUNCOES_DIR / "CNPJ"

for _dir in [str(AUXILIARES_DIR), str(TABELA_PRODUTOS_DIR)]:
    if _dir not in sys.path:
        sys.path.insert(0, _dir)

from conectar_oracle import conectar as conectar_oracle
from ler_sql import ler_sql
from extrair_parametros import extrair_parametros_sql


@dataclass
class ResultadoPipeline:
    ok: bool
    cnpj: str
    mensagens: list[str] = field(default_factory=list)
    arquivos_gerados: list[str] = field(default_factory=list)
    erros: list[str] = field(default_factory=list)


TABELAS_DISPONIVEIS: list[dict[str, str]] = [
    {"id": "produtos_unidades", "nome": "Produtos por Unidade", "descricao": "Tabela base de movimentações por unidade com compras, vendas e co_sefin_item.", "modulo": "produtos_unidades", "funcao": "gerar_produtos_unidades"},
    {"id": "produtos", "nome": "Produtos Normalizados", "descricao": "Agrupa produtos por descrição normalizada e consolida listas de atributos.", "modulo": "produtos", "funcao": "gerar_tabela_produtos"},
    {"id": "produtos_agrupados", "nome": "Produtos Agrupados", "descricao": "Agrupamento manual/final com descr_padrao, co_sefin_padrao e lista_unidades.", "modulo": "produtos_agrupados", "funcao": "gerar_produtos_agrupados"},
    {"id": "produtos_final", "nome": "Produtos Final", "descricao": "Tabela derivada de produtos_agrupados com vínculo produto → agrupamento final.", "modulo": "produtos_agrupados", "funcao": "gerar_produtos_agrupados"},
    {"id": "fatores_conversao", "nome": "Fatores de Conversão", "descricao": "Calcula fatores por unidade a partir de produtos_final e preços médios.", "modulo": "fatores_conversao", "funcao": "gerar_fatores_conversao"},
]

TABELAS_LEGADAS_SUBSTITUIDAS = {
    "tabela_itens_caracteristicas": "produtos_unidades",
    "tabela_descricoes": "produtos",
    "tabela_codigos": "produtos_agrupados",
    "tabela_codigos_mais_descricoes": "produtos_agrupados",
    "fator_conversao": "fatores_conversao",
}

ORDEM_OFICIAL = ["produtos_unidades", "produtos", "produtos_agrupados", "produtos_final", "fatores_conversao"]


class ServicoExtracao:
    def __init__(self, consultas_dir: Path = CONSULTAS_FONTE_DIR, cnpj_root: Path = CNPJ_ROOT):
        self.consultas_dir = consultas_dir
        self.cnpj_root = cnpj_root

    def listar_consultas(self) -> list[Path]:
        if not self.consultas_dir.exists():
            return []
        return sorted([p for p in self.consultas_dir.iterdir() if p.is_file() and p.suffix.lower() == ".sql"], key=lambda p: p.name.lower())

    def pasta_cnpj(self, cnpj: str) -> Path:
        return self.cnpj_root / cnpj

    def pasta_parquets(self, cnpj: str) -> Path:
        pasta = self.pasta_cnpj(cnpj) / "arquivos_parquet"
        pasta.mkdir(parents=True, exist_ok=True)
        return pasta

    @staticmethod
    def sanitizar_cnpj(cnpj: str) -> str:
        digitos = re.sub(r"\D", "", cnpj or "")
        if len(digitos) != 14:
            raise ValueError("Informe um CNPJ com 14 dígitos.")
        return digitos

    @staticmethod
    def montar_binds(sql_text: str, valores: dict[str, Any]) -> dict[str, Any]:
        parametros = extrair_parametros_sql(sql_text)
        valores_lower = {k.lower(): v for k, v in valores.items()}
        return {nome: valores_lower.get(nome.lower()) for nome in parametros}

    def executar_consultas(self, cnpj: str, consultas: list[Path], data_limite: str | None = None, progresso: Callable[[str], None] | None = None) -> list[str]:
        def _msg(texto: str):
            if progresso:
                progresso(texto)

        cnpj = self.sanitizar_cnpj(cnpj)
        pasta = self.pasta_parquets(cnpj)
        arquivos: list[str] = []

        _msg("Conectando ao Oracle...")
        conn = conectar_oracle()
        if conn is None:
            raise RuntimeError("Falha ao conectar ao Oracle. Verifique credenciais e VPN.")

        try:
            for sql_path in consultas:
                nome_consulta = sql_path.stem.lower()
                _msg(f"Executando {sql_path.name}...")
                sql_text = ler_sql(sql_path)
                if sql_text is None:
                    _msg(f"⚠️ Não foi possível ler {sql_path.name}")
                    continue

                binds = self.montar_binds(sql_text, {
                    "CNPJ": cnpj,
                    "cnpj": cnpj,
                    "data_limite_processamento": data_limite,
                    "DATA_LIMITE_PROCESSAMENTO": data_limite,
                })
                try:
                    with conn.cursor() as cursor:
                        cursor.arraysize = 50_000
                        cursor.prefetchrows = 50_000
                        cursor.execute(sql_text, binds)
                        colunas = [desc[0].lower() for desc in cursor.description]
                        todas_linhas: list[tuple] = []
                        while True:
                            lote = cursor.fetchmany(50_000)
                            if not lote:
                                break
                            todas_linhas.extend(lote)
                            _msg(f"  {sql_path.name}: {len(todas_linhas):,} linhas lidas...")
                    if todas_linhas:
                        try:
                            registros = [dict(zip(colunas, row)) for row in todas_linhas]
                            df = pl.DataFrame(registros, infer_schema_length=min(len(registros), 50000))
                        except Exception:
                            dados = {col_name: [row[i] for row in todas_linhas] for i, col_name in enumerate(colunas)}
                            try:
                                df = pl.DataFrame(dados)
                            except Exception:
                                dados_string = {col_name: [str(row[i]) if row[i] is not None else None for row in todas_linhas] for i, col_name in enumerate(colunas)}
                                df = pl.DataFrame(dados_string)
                    else:
                        df = pl.DataFrame({col: [] for col in colunas})
                    arquivo_saida = pasta / f"{nome_consulta}_{cnpj}.parquet"
                    df.write_parquet(arquivo_saida, compression="snappy")
                    arquivos.append(str(arquivo_saida))
                    _msg(f"✅ {sql_path.name}: {df.height:,} linhas → {arquivo_saida.name}")
                except Exception as exc:
                    _msg(f"❌ Erro em {sql_path.name}: {exc}")
        finally:
            conn.close()
        return arquivos


class ServicoTabelas:
    @staticmethod
    def listar_tabelas() -> list[dict[str, str]]:
        return TABELAS_DISPONIVEIS[:]

    @staticmethod
    def gerar_tabelas(cnpj: str, tabelas_selecionadas: list[str], progresso: Callable[[str], None] | None = None) -> list[str]:
        def _msg(texto: str):
            if progresso:
                progresso(texto)

        from pipeline_produtos import executar_pipeline_produtos

        cnpj = re.sub(r"\D", "", cnpj)
        pasta_cnpj = CNPJ_ROOT / cnpj

        legadas = [t for t in tabelas_selecionadas if t in TABELAS_LEGADAS_SUBSTITUIDAS]
        if legadas:
            _msg("ℹ️ Seleções legadas detectadas: " + ", ".join(f"{t}→{TABELAS_LEGADAS_SUBSTITUIDAS[t]}" for t in legadas))

        geradas = executar_pipeline_produtos(cnpj, pasta_cnpj, tabelas_selecionadas=tabelas_selecionadas)
        if not geradas and tabelas_selecionadas:
            raise RuntimeError("Falha ao executar o pipeline oficial de produtos.")

        _msg("✅ Pipeline oficial concluído. Tabelas geradas: " + ", ".join(geradas) if geradas else "⚠️ Nenhuma tabela gerada.")
        return geradas


class ServicoPipelineCompleto:
    def __init__(self):
        self.servico_extracao = ServicoExtracao()
        self.servico_tabelas = ServicoTabelas()

    def executar_completo(self, cnpj: str, consultas: list[Path], tabelas: list[str], data_limite: str | None = None, progresso: Callable[[str], None] | None = None) -> ResultadoPipeline:
        cnpj = ServicoExtracao.sanitizar_cnpj(cnpj)
        resultado = ResultadoPipeline(ok=True, cnpj=cnpj)

        def _msg(texto: str):
            resultado.mensagens.append(texto)
            if progresso:
                progresso(texto)

        if consultas:
            _msg(f"═══ Fase 1: Extração Oracle ({len(consultas)} consultas) ═══")
            try:
                resultado.arquivos_gerados.extend(self.servico_extracao.executar_consultas(cnpj, consultas, data_limite, _msg))
            except Exception as exc:
                resultado.erros.append(f"Falha na extração: {exc}")
                resultado.ok = False
                return resultado

        if tabelas:
            _msg(f"═══ Fase 2: Geração de tabelas ({len(tabelas)} selecionadas) ═══")
            try:
                resultado.arquivos_gerados.extend(self.servico_tabelas.gerar_tabelas(cnpj, tabelas, _msg))
            except Exception as exc:
                resultado.erros.append(f"Falha na geração de tabelas: {exc}")
                resultado.ok = False

        if resultado.ok:
            _msg(f"═══ Pipeline concluído para CNPJ {cnpj} ═══")
        return resultado
