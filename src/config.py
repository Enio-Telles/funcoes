import os
from pathlib import Path
from dotenv import load_dotenv

# Root do projeto
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Carrega variáveis de ambiente (.env)
env_path = PROJECT_ROOT / ".env"
load_dotenv(env_path, override=False, encoding="utf-8")

# Nome do App
APP_NAME = "Fiscal Parquet Analyzer"

# Configurações de Caminhos (Baseadas no PROJECT_ROOT por padrão)
# Auditoria: Permitir override por variável de ambiente para portabilidade
FUNCOES_ROOT = Path(os.getenv("FUNCOES_ROOT", PROJECT_ROOT))

DIR_DADOS = FUNCOES_ROOT / "dados"
DIR_REFERENCIAS = FUNCOES_ROOT / "referencias"
SQL_DIR = FUNCOES_ROOT / "sql"
CONSULTAS_FONTE_DIR = FUNCOES_ROOT / "sql"
CONSULTAS_ROOT = SQL_DIR

# Subdiretórios específicos
CNPJ_ROOT = DIR_DADOS
TABELA_PRODUTOS_DIR = DIR_DADOS
CFOP_BI_PATH = DIR_REFERENCIAS / "cfop_bi.parquet"

# Configurações de Banco de Dados
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_DSN = os.getenv("DB_DSN")

# Configurações de Exportação e UI
DEFAULT_PAGE_SIZE = 50
MAX_DOCX_ROWS = 5000  # Limite para evitar travamentos em tabelas Word gigantes

# Caminho do Orquestrador
PIPELINE_SCRIPT = PROJECT_ROOT / "src" / "orquestrador.py"

# Estado e Registro
APP_STATE_ROOT = FUNCOES_ROOT / "workspace" / "app_state"
REGISTRY_FILE = APP_STATE_ROOT / "cnpjs.json"

# Logs
LOG_DIR = FUNCOES_ROOT / "logs"
AGGREGATION_LOG_FILE = LOG_DIR / "aggregation.log"

def inicializar_diretorios():
    """
    Cria a estrutura de pastas necessária para o funcionamento do app.
    """
    diretorios = [
        DIR_DADOS,
        DIR_REFERENCIAS,
        SQL_DIR,
        LOG_DIR,
        FUNCOES_ROOT / "workspace",
        FUNCOES_ROOT / "workspace" / "app_state"
    ]
    for d in diretorios:
        d.mkdir(parents=True, exist_ok=True)
