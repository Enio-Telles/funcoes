from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

# Refatoração 3: Chamada Direta ao invés de Subprocesso
# Importamos as funções do orquestrador para execução eficiente e melhor rastreio
from src.orquestrador import executar_pipeline_completo

# Importar constantes do config
from src.config import SQL_DIR, CNPJ_ROOT

@dataclass
class PipelineResult:
    ok: bool
    stdout: str = "" # Mantido para compatibilidade, mas agora vazio ou com logs capturados
    stderr: str = ""
    cnpj: str = ""
    returncode: int = 0

class PipelineService:
    def __init__(self, sql_dir: Path = SQL_DIR, output_root: Path = CNPJ_ROOT) -> None:
        """
        Serviço para disparar o orquestrador via chamada direta de função.
        output_root padrão é CNPJ_ROOT (dados/CNPJ).
        """
        self.sql_dir = sql_dir
        self.output_root = output_root

    @staticmethod
    def sanitize_cnpj(cnpj: str) -> str:
        digits = re.sub(r"\D", "", cnpj or "")
        if len(digits) != 14:
            raise ValueError("Informe um CNPJ com 14 dígitos.")
        return digits

    def _run_internal(self, cnpj: str, apenas_extrair: bool = False, apenas_processar: bool = False, data_limite: str | None = None) -> PipelineResult:
        """
        Executa o pipeline chamando diretamente a função do orquestrador.
        Refatoração 3.1: Melhoria de performance e compartilhamento de memória.
        """
        cnpj = self.sanitize_cnpj(cnpj)
        
        try:
            # Chamada direta
            sucesso = executar_pipeline_completo(
                cnpj=cnpj,
                data_limite=data_limite,
                pasta_sql_path=self.sql_dir,
                pasta_dados_path=self.output_root,
                apenas_extrair=apenas_extrair,
                apenas_processar=apenas_processar
            )
            
            return PipelineResult(
                ok=sucesso,
                cnpj=cnpj,
                returncode=0 if sucesso else 1,
                stdout="Execução direta concluída."
            )
        except Exception as e:
            return PipelineResult(
                ok=False,
                cnpj=cnpj,
                stderr=str(e),
                returncode=1
            )

    def run_full_pipeline(self, cnpj: str, data_limite: str | None = None) -> PipelineResult:
        """Executa extração + processamento."""
        return self._run_internal(cnpj, data_limite=data_limite)

    def run_extraction(self, cnpj: str, data_limite: str | None = None) -> PipelineResult:
        """Executa apenas a extração do Oracle."""
        return self._run_internal(cnpj, apenas_extrair=True, data_limite=data_limite)

    def run_processing(self, cnpj: str) -> PipelineResult:
        """Executa apenas o processamento dos arquivos locais."""
        return self._run_internal(cnpj, apenas_processar=True)

    def delete_cnpj_all(self, cnpj: str) -> bool:
        """
        Exclui toda a pasta do CNPJ em dados/CNPJ com tratamento para Windows.
        Refatoração 3.2: Prevenção de PermissionError.
        """
        cnpj = self.sanitize_cnpj(cnpj)
        pasta = self.output_root / cnpj
        if pasta.exists() and pasta.is_dir():
            try:
                shutil.rmtree(pasta)
                return True
            except PermissionError:
                # Se falhar por arquivo aberto, tentamos avisar ou ignorar (conforme requisito)
                # Opção: shutil.rmtree(pasta, ignore_errors=True)
                raise PermissionError(f"Não foi possível excluir '{pasta}'. Verifique se algum arquivo .parquet está aberto no Excel ou Polars.")
        return False

    def delete_processed_data(self, cnpj: str) -> bool:
        """Exclui apenas a pasta 'analises' do CNPJ."""
        cnpj = self.sanitize_cnpj(cnpj)
        pasta_analises = self.output_root / cnpj / "analises"
        if pasta_analises.exists() and pasta_analises.is_dir():
            try:
                shutil.rmtree(pasta_analises)
                return True
            except PermissionError:
                raise PermissionError(f"Não foi possível excluir '{pasta_analises}'. Feche os arquivos abertos e tente novamente.")
        return False
