import oracledb
import polars as pl
from contextlib import contextmanager
from typing import Generator, Any, Dict, Optional
import os
import logging

logger = logging.getLogger("sefin_audit_python.db_manager")

class DatabaseManager:
    """
    Gestor de ligações à base de dados com Context Manager para garantir
    a libertação de recursos e segurança contra SQL Injection via bindings.
    """
    def __init__(self, dsn: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None):
        """
        Inicializa o gerenciador. Se os parâmetros não forem fornecidos, 
        tenta buscá-los das variáveis de ambiente.
        """
        self.dsn = dsn or os.getenv("ORACLE_DSN")
        self.user = user or os.getenv("ORACLE_USER")
        self.password = password or os.getenv("ORACLE_PASSWORD")

    @contextmanager
    def get_connection(self) -> Generator[oracledb.Connection, None, None]:
        """
        Garante a abertura e fecho seguro da ligação.
        Uso: with db_manager.get_connection() as conn: ...
        """
        conn = None
        try:
            conn = oracledb.connect(user=self.user, password=self.password, dsn=self.dsn)
            
            # Padroniza pontuação de números na sessão para prevenir problemas de casting
            with conn.cursor() as cursor:
                cursor.execute("ALTER SESSION SET NLS_NUMERIC_CHARACTERS = '.,'")
                
            yield conn
        except Exception as e:
            logger.error(f"Erro na conexão com Oracle: {e}")
            raise
        finally:
            if conn is not None:
                conn.close()

    def fetch_to_polars(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> pl.DataFrame:
        """
        Executa uma query de forma segura (com bindings) e devolve diretamente um Polars DataFrame.
        """
        params = parameters or {}
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            cols = [col[0] for col in cursor.description]
            data = cursor.fetchall()
            
            return pl.DataFrame(data, schema=cols, orient="row", strict=False)
