"""
Teste de Verificação e Performance para Cruzamentos Multi-CNPJ.
Valida se o loader consegue carregar arquivos de diferentes pastas e se o DuckDB opera sobre eles.
"""
from pathlib import Path
import polars as pl
import time
from rich import print as rprint
from cruzamentos.core.multi_cnpj_loader import carregar_tabelas_multi_cnpj, criar_contexto_sql

def testar_integridade_e_performance():
    rprint("[bold yellow]🧪 Iniciando testes de sistema...[/bold yellow]")
    
    # 1. Teste de listagem dinâmica (sem passar CNPJs)
    try:
        start_time = time.perf_counter()
        
        # Testamos carregar a reg_0200 (base cadastral) de todos os CNPJs
        lf_0200 = carregar_tabelas_multi_cnpj("reg_0200", pasta="arquivos_parquet")
        
        # Coletar os primeiros resultados para garantir que funciona
        df_sample = lf_0200.head(10).collect()
        
        load_time = time.perf_counter() - start_time
        rprint(f"[green]✅ Carregamento Lazy bem-sucedido ({load_time:.4f}s)![/green]")
        rprint(f"Amostra de dados (10 linhas):\n{df_sample}")
        
        # 2. Teste de consulta SQL via DuckDB
        con = criar_contexto_sql({"cadastro": lf_0200})
        
        # Contagem de itens por CNPJ
        query = "SELECT cnpj_origem, count(*) as total_itens FROM cadastro GROUP BY 1 ORDER BY 2 DESC"
        df_res = con.execute(query).pl()
        
        rprint("[blue]📊 Distribuição de itens por CNPJ:[/blue]")
        rprint(df_res)
        
        rprint("[bold green]✨ Todos os sistemas operacionais. Infraestrutura pronta para uso.[/bold green]")
        
    except FileNotFoundError as e:
        rprint(f"[yellow]⚠️  Aviso: {e}[/yellow]")
        rprint("Dica: Certifique-se de que existem arquivos '.parquet' nas pastas de CNPJ.")
    except Exception as e:
        rprint(f"[bold red]❌ Falha no teste:[/bold red] {e}")

if __name__ == "__main__":
    testar_integridade_e_performance()
