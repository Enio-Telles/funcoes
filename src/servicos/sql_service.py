import re
from dataclasses import dataclass
from pathlib import Path
from typing import Set

# Constantes para UI
WIDGET_DATE = "date"
WIDGET_TEXT = "text"

@dataclass
class ParamInfo:
    name: str
    widget_type: str = WIDGET_TEXT
    default_value: str = ""

class SQLService:
    def __init__(self, sql_dir: Path):
        self.sql_dir = sql_dir

    def list_available_queries(self) -> list[str]:
        if not self.sql_dir.exists():
            return []
        return [f.stem for f in self.sql_dir.glob("*.sql")]

    def read_query(self, query_name: str) -> str:
        sql_path = self.sql_dir / f"{query_name}.sql"
        if not sql_path.exists():
            raise FileNotFoundError(f"Arquivo SQL não encontrado: {sql_path}")
        return sql_path.read_text(encoding="utf-8")

    @staticmethod
    def extract_params(sql_text: str) -> Set[str]:
        """
        Extrai nomes de parâmetros bind (ex: :cnpj) do texto SQL.
        Refatoração: Ignora comentários e strings literais para evitar falsos-positivos.
        """
        # 1. Remover comentários de bloco /* ... */
        sql_clean = re.sub(r"/\*.*?\*/", "", sql_text, flags=re.DOTALL)
        
        # 2. Remover comentários de linha -- ...
        sql_clean = re.sub(r"--.*", "", sql_clean)
        
        # 3. Remover strings literais '...'
        sql_clean = re.sub(r"'.*?'", "''", sql_clean)

        # 4. Capturar binds
        pattern = r"(?<!\[):([A-Za-z_]\w*)"
        matches = re.findall(pattern, sql_clean)
        
        return {m.lower() for m in matches}
