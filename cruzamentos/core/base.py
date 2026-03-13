from abc import ABC, abstractmethod
import polars as pl
from pathlib import Path
from typing import Dict, Any, List
import logging
import sys

# Garante que podemos importar config.py da raiz do projeto
_CRUZAMENTOS_CORE_DIR = Path(__file__).resolve().parent
_CRUZAMENTOS_DIR = _CRUZAMENTOS_CORE_DIR.parent
_PROJETO_DIR = _CRUZAMENTOS_DIR.parent

if str(_PROJETO_DIR) not in sys.path:
    sys.path.insert(0, str(_PROJETO_DIR))

from config import obter_diretorios_cnpj

logger = logging.getLogger("sefin_audit_engine.core")

class BaseCruzamentoFiscal(ABC):
    """
    Padrão Strategy + Template Method para padronizar todos os cruzamentos fiscais.
    Força a utilização de Polars LazyFrames para prevenir Out-of-Memory (OOM).
    """

    def __init__(self, cnpj: str):
        # Sanitização básica de input para prevenir Path Traversal
        cnpj_str = str(cnpj)
        cnpj_limpo = "".join(filter(str.isdigit, cnpj_str))
        
        if not cnpj_limpo or len(cnpj_limpo) != 14:
            raise ValueError(f"CNPJ inválido: {cnpj_str}")
            
        self.cnpj = cnpj_limpo
        
        dir_parquet, dir_analises, _ = obter_diretorios_cnpj(self.cnpj)
        
        self.base_dir = dir_parquet
        self.output_dir = dir_analises

    def carregar_lazy(self, nome_arquivo: str) -> pl.LazyFrame:
        """
        Centraliza o I/O, garantindo leitura Lazy do Parquet.
        Isto cria um grafo computacional sem carregar os dados para a RAM.
        """
        caminho_completo = self.base_dir / nome_arquivo
        if not caminho_completo.exists():
            logger.error(f"Ficheiro não encontrado: {caminho_completo}")
            raise FileNotFoundError(f"Dados em falta para o CNPJ {self.cnpj}: {nome_arquivo}")
        
        # scan_parquet é fundamental para otimização de memória
        return pl.scan_parquet(caminho_completo)

    @abstractmethod
    def construir_plano_execucao(self, **kwargs) -> pl.LazyFrame:
        """
        As classes filhas DEVEM implementar este método contendo apenas
        operações Polars Lazy (select, filter, join, with_columns).
        Não pode conter chamadas .collect() no seu interior.
        """
        pass

    def executar_e_guardar(self, nome_saida: str, **kwargs) -> Dict[str, Any]:
        """
        Template Method: Executa o plano (Streaming/Multithread) e guarda o resultado.
        """
        caminho_saida = self.output_dir / nome_saida
        
        try:
            logger.info(f"Iniciando cruzamento para CNPJ: {self.cnpj} -> {nome_saida}")
            
            # 1. Obtém o grafo computacional
            plano_lazy = self.construir_plano_execucao(**kwargs)
            
            # 2. Executa o plano otimizado de forma *Eager* (processamento real)
            # Utilizamos streaming=True para lidar com ficheiros que excedam a RAM
            df_resultado = plano_lazy.collect(streaming=True)
            
            # 3. Guarda em formato colunar comprimido (ZSTD recomendado para Data Lakes)
            df_resultado.write_parquet(caminho_saida, compression="zstd")
            
            linhas = df_resultado.height
            logger.info(f"Cruzamento concluído com sucesso. Linhas: {linhas}")
            
            return {
                "status": "success",
                "linhas_processadas": linhas,
                "ficheiro_saida": str(caminho_saida)
            }
            
        except Exception as e:
            logger.exception("Falha na execução do cruzamento fiscal.")
            return {
                "status": "error",
                "mensagem": str(e)
            }

    def _filtro_data(self, coluna_data: str, data_inicio: str = None, data_fim: str = None) -> pl.Expr:
        """Helper para aplicar filtros de data de forma segura dentro das expressões Lazy."""
        import datetime
        expr = pl.lit(True) # Filtro neutro por defeito
        if data_inicio:
            expr = expr & (pl.col(coluna_data) >= pl.date(data_inicio))
        if data_fim:
            expr = expr & (pl.col(coluna_data) <= pl.date(data_fim))
        return expr
