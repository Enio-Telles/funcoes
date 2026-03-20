import argparse
import polars as pl
from pathlib import Path
from rich import print as rprint
import sys

# Importar constantes do config
from src.config import SQL_DIR, CNPJ_ROOT as DIR_DADOS, DIR_REFERENCIAS

# Importar ferramentas de extração e utilitários
from src.extracao.extrator import extrair_por_cnpj
from src.utilitarios.parquet_utils import salvar_para_parquet

# Importar NOVAS funções de transformação modular
from src.transformacao.produtos_unidades import gerar_tabela_produtos_unidades
from src.transformacao.produtos import gerar_tabela_produtos_normalizados
from src.transformacao.produtos_agrupados import produtos_agrupados
from src.transformacao.fatores_conversao import calcular_fatores_conversao

# Importar transformações secundárias (manter se necessário)
from src.transformacao.analise_produtos.documentos import processar_tabela_documentos

def executar_extrair(cnpj: str, data_limite: str, caminho_sql: Path, caminho_dados_raiz: Path) -> bool:
    """Etapa 1: Extração de Dados Brutos."""
    rprint(f"[cyan]Extraindo dados do Oracle para o CNPJ {cnpj}... [/cyan]")
    return extrair_por_cnpj(
        cnpj=cnpj, 
        data_limite=data_limite, 
        pasta_consultas=caminho_sql, 
        pasta_base_saida=caminho_dados_raiz
    )

def executar_processar(cnpj: str, caminho_dados_raiz: Path) -> bool:
    """Etapa 2: Transformação Modular e Enriquecimento."""
    rprint(f"[yellow]Iniciando redesign modular de produtos para CNPJ: {cnpj}[/yellow]")
    
    pasta_tabelas = caminho_dados_raiz / cnpj / "tabelas_brutas"
    pasta_analises = caminho_dados_raiz / cnpj / "analises" / "produtos"
    pasta_analises.mkdir(parents=True, exist_ok=True)
    
    def _ler_tab(nome):
        p = pasta_tabelas / f"{nome}_{cnpj}.parquet"
        if not p.exists(): 
            return None
        return pl.read_parquet(p)

    # 1. Carregar Dados Brutos
    df_c100 = _ler_tab("c100")
    df_c170 = _ler_tab("c170")
    df_nfe = _ler_tab("nfe")
    df_nfce = _ler_tab("nfce")
    df_bloco_h = _ler_tab("bloco_h")
    
    # Carregar Referência de CFOP para classificação de compras/vendas
    p_cfop = DIR_REFERENCIAS / "cfop_bi.parquet"
    df_cfop_ref = pl.read_parquet(p_cfop) if p_cfop.exists() else None

    if df_c170 is None and df_nfe is None:
        rprint("[red]❌ Dados críticos (C170/NFe) não encontrados. Execute a extração primeiro.[/red]")
        return False

    # 2. Unificar Unidades (Módulo 1)
    rprint("[cyan]Módulo 1: Gerando tabela base de unidades (Movimentação)...[/cyan]")
    df_unidades = gerar_tabela_produtos_unidades(
        cnpj=cnpj,
        df_c170=df_c170,
        df_nfe_itens=df_nfe,
        df_nfce_itens=df_nfce,
        df_bloco_h=df_bloco_h,
        df_cfop_ref=df_cfop_ref
    )
    
    # 3. Normalizar e Agrupar Produtos (Módulo 2)
    rprint("[cyan]Módulo 2: Normalizando descrições e gerando chaves de produto...[/cyan]")
    df_produtos = gerar_tabela_produtos_normalizados(df_unidades)
    
    # 4. Agrupamento Final e Heurísticas (Módulo 3)
    rprint("[cyan]Módulo 3: Aplicando heurística de atributos padrão (NCM, CEST, GTIN)...[/cyan]")
    # Nota: df_manual poderia vir de uma tabela editável persistida
    df_final = produtos_agrupados(df_produtos, df_manual=None)
    
    # 5. Cálculo de Fatores de Conversão (Módulo 4)
    rprint("[cyan]Módulo 4: Calculando fatores de conversão entre unidades...[/cyan]")
    df_fatores = calcular_fatores_conversao(df_unidades, df_final)
    
    # Processamento de Documentos (Opcional/Secundário)
    df_docs = processar_tabela_documentos(df_nfe) if df_nfe is not None else None

    # 6. Salvar Resultados
    rprint("[yellow]Salvando resultados do redesign modular...[/yellow]")
    salvar_para_parquet(df_unidades, pasta_analises / f"tabela_unidades_base_{cnpj}.parquet")
    salvar_para_parquet(df_produtos, pasta_analises / f"tabela_produtos_consolidada_{cnpj}.parquet")
    salvar_para_parquet(df_final, pasta_analises / f"tabela_produtos_final_{cnpj}.parquet")
    salvar_para_parquet(df_fatores, pasta_analises / f"tabela_fatores_conversao_{cnpj}.parquet")
    
    if df_docs is not None:
         salvar_para_parquet(df_docs, pasta_analises / f"tabela_documentos_{cnpj}.parquet")
    
    rprint(f"[bold green]✅ Processamento concluído: {df_final.height} produtos únicos identificados.[/bold green]")
    return True

def executar_pipeline_completo(cnpj: str, data_limite: str = None, pasta_sql_path: Path = None, pasta_dados_path: Path = None, apenas_extrair: bool = False, apenas_processar: bool = False):
    """
    Orquestrador que gerencia a execução parcial ou total do pipeline.
    """
    rprint(f"[bold green]🚀 Iniciando pipeline para CNPJ: {cnpj}[/bold green]")
    
    caminho_sql = pasta_sql_path or SQL_DIR
    caminho_dados_raiz = pasta_dados_path or DIR_DADOS
    
    executar_tudo = not (apenas_extrair or apenas_processar)

    if apenas_extrair or executar_tudo:
        sucesso = executar_extrair(cnpj, data_limite, caminho_sql, caminho_dados_raiz)
        if not sucesso:
            rprint("[red]❌ Falha na etapa de extração.[/red]")
            return False

    if apenas_processar or executar_tudo:
        sucesso = executar_processar(cnpj, caminho_dados_raiz)
        if not sucesso:
            rprint("[red]❌ Falha na etapa de processamento.[/red]")
            return False

    rprint(f"[bold green]✅ Pipeline concluído com sucesso para o CNPJ: {cnpj}[/bold green]")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Orquestrador do Pipeline de Auditoria")
    parser.add_argument("--cnpj", required=True, help="CNPJ para processar (14 dígitos)")
    parser.add_argument("--data-limite", help="Data limite EFD (DD/MM/YYYY)")
    parser.add_argument("--sql-dir", help="Pasta com arquivos .sql")
    parser.add_argument("--saida", help="Pasta base para saída de dados")
    parser.add_argument("--apenas-extrair", action="store_true", help="Executa apenas a extração do banco")
    parser.add_argument("--apenas-processar", action="store_true", help="Executa apenas o processamento dos parquets locais")
    
    args = parser.parse_args()
    
    p_sql = Path(args.sql_dir) if args.sql_dir else None
    p_saida = Path(args.saida) if args.saida else None
    
    executar_pipeline_completo(
        cnpj=args.cnpj,
        data_limite=args.data_limite,
        pasta_sql_path=p_sql,
        pasta_dados_path=p_saida,
        apenas_extrair=args.apenas_extrair,
        apenas_processar=args.apenas_processar
    )
