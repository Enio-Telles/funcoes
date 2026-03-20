import polars as pl
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from rich import print as rprint
from .conexao import conectar
from .leitor_sql import ler_sql
from .extrair_parametros import extrair_parametros_sql

def processar_arquivo_sql(arq_sql: Path, consultas_dir: Path, pasta_saida: Path, cnpj: str, data_limite: str):
    """
    Executa uma consulta SQL no Oracle e salva o resultado em um arquivo Parquet usando chunks para evitar OOM.
    Refatoração 2: Memória (fetchmany) + Validação de Binds + Path Safe.
    """
    try:
        # Refatoração 2.2: Path Safe
        try:
            caminho_relativo = arq_sql.relative_to(consultas_dir)
        except ValueError:
            # Caso o SQL não esteja dentro do diretório de consultas esperado
            caminho_relativo = Path(arq_sql.name)
            
        nome_tabela = arq_sql.stem.lower()
        arquivo_saida = pasta_saida / f"{nome_tabela}_{cnpj}.parquet"

        sql_text = ler_sql(arq_sql)
        if not sql_text:
            rprint(f"[red]Erro ao ler arquivo SQL: {arq_sql}[/red]")
            return

        # Refatoração 2.3: Validação de Binds
        binds_necessarios = extrair_parametros_sql(sql_text)
        valores_disponiveis = {
            "cnpj": cnpj,
            "data_limite_processamento": data_limite
        }
        
        # Validar se todas as variáveis da query estão no dicionário
        for bind in binds_necessarios:
            if bind.lower() not in [v.lower() for v in valores_disponiveis.keys()]:
                rprint(f"[red]Erro: Bind '{bind}' exigido na query '{nome_tabela}' não foi fornecido.[/red]")
                return
            # Se for data_limite_processamento e estiver nulo, podemos ter erro no Oracle dependendo da query
            if bind.lower() == "data_limite_processamento" and not data_limite:
                rprint(f"[yellow]Aviso: Query '{nome_tabela}' exige data_limite, mas o valor é nulo.[/yellow]")

        with conectar() as conn:
            with conn.cursor() as cursor:
                # Refatoração 2.1: Chunked Extraction (Prevenção de OOM)
                # Ajustamos arraysize para performance de rede e fetchmany para RAM
                cursor.arraysize = 50_000 
                cursor.execute(sql_text, {k: v for k, v in valores_disponiveis.items() if k in [b.lower() for b in binds_necessarios]})
                
                colunas = [desc[0].lower() for desc in cursor.description]
                
                # Vamos ler em blocos e concatenar no Polars
                chunks = []
                total_linhas = 0
                
                while True:
                    rows = cursor.fetchmany(50_000)
                    if not rows:
                        break
                    
                    # Cria DataFrame do chunk
                    chunk_df = pl.DataFrame([dict(zip(colunas, row)) for row in rows], infer_schema_length=50000)
                    chunks.append(chunk_df)
                    total_linhas += len(rows)
                    # Opcional: rprint(f"  {nome_tabela}: {total_linhas:,} linhas lidas...")

                if chunks:
                    df_final = pl.concat(chunks)
                    arquivo_saida.parent.mkdir(parents=True, exist_ok=True)
                    df_final.write_parquet(arquivo_saida, compression="snappy")
                    rprint(f"[green]✔ {nome_tabela} extraído ({total_linhas:,} linhas).[/green]")
                else:
                    # Salva tabela vazia com as colunas corretas
                    df_vazio = pl.DataFrame({col: [] for col in colunas})
                    df_vazio.write_parquet(arquivo_saida)
                    rprint(f"[yellow]! {nome_tabela} extraída (0 linhas).[/yellow]")

    except Exception as e:
        rprint(f"[red]Erro ao extrair {arq_sql.name}: {e}[/red]")

def extrair_por_cnpj(cnpj: str, data_limite: str, pasta_consultas: Path, pasta_base_saida: Path):
    """
    Gerencia a extração concorrente de múltiplos arquivos SQL.
    """
    pasta_saida = pasta_base_saida / cnpj / "tabelas_brutas"
    pasta_saida.mkdir(parents=True, exist_ok=True)

    arquivos_sql = list(pasta_consultas.glob("*.sql"))
    if not arquivos_sql:
        rprint("[yellow]Nenhum arquivo .sql encontrado.[/yellow]")
        return False

    rprint(f"[bold]Iniciando extração para {cnpj} ({len(arquivos_sql)} tabelas)...[/bold]")
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        for arq in arquivos_sql:
            executor.submit(processar_arquivo_sql, arq, pasta_consultas, pasta_saida, cnpj, data_limite)

    return True
