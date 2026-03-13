import logging
import polars as pl
import re
from pathlib import Path
from fastapi import APIRouter, HTTPException

logger = logging.getLogger("sefin_audit_python")
router = APIRouter(prefix="/api/python/references", tags=["references"])

_PROJETO_DIR = Path(__file__).resolve().parent.parent.parent.parent
_REF_DIR = _PROJETO_DIR / "referencias"

@router.get("/ncm/{codigo}")
async def get_ncm_details(codigo: str):
    """Busca detalhes do NCM (Capítulo, Posição, Descrição)."""
    # Voltando para tabela_ncm.parquet conforme solicitado pelo usuário
    ncm_path = _REF_DIR / "NCM" / "tabela_ncm.parquet"
    if not ncm_path.exists():
        # Fallback para o postgres se a principal não existir
        ncm_path = _REF_DIR / "NCM" / "ncm_postgres.parquet"
        
    if not ncm_path.exists():
        raise HTTPException(status_code=404, detail="Tabela NCM não encontrada.")
    
    try:
        codigo_limpo = re.sub(r"[^0-9]", "", codigo)
        df = pl.read_parquet(str(ncm_path))
        
        # Detecção automática de colunas (tabela_ncm usa CamelCase, ncm_postgres usa minúsculas)
        cols = df.columns
        def get_col(options):
            for opt in options:
                if opt in cols: return opt
            return options[0]

        col_codigo = get_col(["Codigo_NCM", "codigo"])
        col_cap = get_col(["Capitulo", "capitulo"])
        col_descr_cap = get_col(["Descr_Capitulo", "descr_capitulo"])
        col_pos = get_col(["Posicao", "posicao"])
        col_descr_pos = get_col(["Descr_Posicao", "descr_posicao"])
        col_desc = get_col(["Descricao", "descricao"])

        # Filtra pelo código NCM
        res = df.filter(pl.col(col_codigo).str.replace_all(r"[^0-9]", "") == codigo_limpo)
        
        if res.is_empty():
            # Busca por prefixo se não achar exato
            res = df.filter(pl.col(col_codigo).str.replace_all(r"[^0-9]", "").str.starts_with(codigo_limpo[:4]))
            if res.is_empty():
                raise HTTPException(status_code=404, detail="NCM não localizado.")
        
        # Ordena para pegar o mais específico (maior comprimento de código)
        try:
            res = res.with_columns(l = pl.col(col_codigo).str.len_chars()).sort("l", descending=True)
        except:
            res = res.with_columns(l = pl.col(col_codigo).str.lengths()).sort("l", descending=True)
            
        item = res.to_dicts()[0]
        
        # Extração de campos
        ncm_val = re.sub(r"[^0-9]", "", str(item.get(col_codigo, "")))
        capitulo = str(item.get(col_cap) or ncm_val[:2])
        posicao = str(item.get(col_pos) or ncm_val[:4])
        
        descr_capitulo = item.get(col_descr_cap) or ""
        descr_posicao = item.get(col_descr_pos) or ""
        
        def is_invalid(v):
            return v is None or str(v).lower() in ['none', 'nan', 'null', '']

        # Busca recursiva se a posição estiver vazia
        if is_invalid(descr_posicao):
            try:
                # 1. Tenta buscar em qualquer linha da PRÓPRIA tabela que tenha essa posição preenchida
                pos_res = df.filter((pl.col(col_pos) == posicao) & (~pl.col(col_descr_pos).is_null())).head(1)
                if not pos_res.is_empty():
                    descr_posicao = pos_res.row(0, named=True).get(col_descr_pos)
                
                # 2. Se ainda não achou, tenta buscar por código de NCM exato da posição na PRÓPRIA tabela
                if is_invalid(descr_posicao):
                    fmt_pos = f"{posicao[:2]}.{posicao[2:]}"
                    exact_res = df.filter(pl.col(col_codigo).is_in([posicao, fmt_pos])).head(1)
                    if not exact_res.is_empty():
                        row = exact_res.row(0, named=True)
                        descr_posicao = row.get(col_desc) or row.get(col_descr_pos)
            except: pass

        # 3. EXTRA FALLBACK: Se ainda assim estiver vazio, tenta carregar do ncm_postgres.parquet (se houver)
        # apenas para preencher o gap de informação técnica de hierarquia
        if is_invalid(descr_posicao) and ncm_path.name == "tabela_ncm.parquet":
            alt_path = _REF_DIR / "NCM" / "ncm_postgres.parquet"
            if alt_path.exists():
                try:
                    df_alt = pl.read_parquet(str(alt_path))
                    # Busca direta pelo código da posição ou pelo código total
                    alt_res = df_alt.filter(
                        (pl.col("codigo").str.replace_all(r"[^0-9]", "") == posicao) |
                        (pl.col("codigo").str.replace_all(r"[^0-9]", "").str.starts_with(posicao))
                    ).sort("descr_posicao", descending=True).head(1)
                    
                    if not alt_res.is_empty():
                        descr_posicao = alt_res.to_dicts()[0].get("descr_posicao")
                except: pass

        # Formatação final conforme solicitado: Capitulo - Descr_Capitulo; Posicao: Descr_Posicao; Codigo_NCM - Descricao
        d_cap = descr_capitulo if not is_invalid(descr_capitulo) else ""
        d_pos = descr_posicao if not is_invalid(descr_posicao) else ""
        
        # Limpa descrição do item (remove dashes iniciais)
        item_desc = str(item.get(col_desc, "")).strip()
        item_desc = re.sub(r"^[-\s]+", "", item_desc)
        
        # Constrói as 3 linhas no formato premium
        formatted_desc = (
            f"Capítulo: {capitulo} - {d_cap}\n"
            f"Posição: {posicao} - {d_pos}\n"
            f"NCM: {item.get(col_codigo)} - {item_desc}"
        )
        
        return {
            "success": True,
            "data": {
                "codigo": item.get(col_codigo),
                "capitulo": capitulo,
                "descr_capitulo": descr_capitulo,
                "posicao": posicao,
                "descr_posicao": descr_posicao,
                "descricao": formatted_desc
            }
        }
        
        return {
            "success": True,
            "data": {
                "codigo": item.get("Codigo_NCM"),
                "capitulo": capitulo,
                "descr_capitulo": descr_capitulo,
                "posicao": posicao,
                "descr_posicao": descr_posicao,
                "descricao": formatted_desc
            }
        }
    except Exception as e:
        logger.error(f"[references] Erro NCM: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cest/{codigo}")
async def get_cest_details(codigo: str):
    """Busca detalhes do CEST (Segmento, NCMs associados, Descrição)."""
    cest_path = _REF_DIR / "CEST" / "cest.parquet"
    seg_path = _REF_DIR / "CEST" / "segmentos_mercadorias.parquet"
    
    if not cest_path.exists():
        raise HTTPException(status_code=404, detail="Tabela CEST não encontrada.")
    
    try:
        codigo_limpo = re.sub(r"[^0-9]", "", codigo)
        df_cest = pl.read_parquet(str(cest_path))
        
        # Filtra pelo CEST (normalizando a coluna na comparação)
        res_cest = df_cest.filter(pl.col("CEST").str.replace_all(r"[^0-9]", "") == codigo_limpo)
        
        if res_cest.is_empty():
            # Tenta busca parcial se não achar exato (ex: 4 ou 7 dígitos)
            res_cest = df_cest.filter(pl.col("CEST").str.replace_all(r"[^0-9]", "").str.starts_with(codigo_limpo[:4]))
            if res_cest.is_empty():
                raise HTTPException(status_code=404, detail="CEST não localizado.")
        
        # Coleta todas as descrições e NCMs associados a este CEST
        descricoes = res_cest.select("DESCRICAO").unique().to_series().to_list()
        ncms = res_cest.select("NCM").unique().to_series().to_list()
        
        # Extrai segmento (2 primeiros dígitos do CEST)
        cest_row = res_cest.row(0, named=True)
        cest_val = re.sub(r"[^0-9]", "", str(cest_row.get("CEST", "")))
        segmento_id = cest_val[:2]
        
        # Busca nome do segmento
        segmento_nome = "Não localizado"
        if seg_path.exists():
            df_seg = pl.read_parquet(str(seg_path))
            res_seg = df_seg.filter(pl.col("Codigo_Segmento") == segmento_id)
            if not res_seg.is_empty():
                segmento_nome = res_seg.row(0, named=True).get("Nome_Segmento", "Não localizado")
        
        # Formatação Segmento: Codigo_Segmento - Nome_Segmento
        seg_formatado = f"Segmento: {segmento_id} - {segmento_nome}"
        
        # Buscar descrição da posição do NCM associado
        ncm_associado = str(ncms[0]) if ncms else ""
        descr_pos_ncm = ""
        if ncm_associado:
            try:
                # Normaliza NCM associado e pega os 4 primeiros dígitos da posição
                ncm_pos_query = re.sub(r"[^0-9]", "", ncm_associado)[:4]
                ncm_ref_path = _REF_DIR / "NCM" / "tabela_ncm.parquet"
                if ncm_ref_path.exists():
                    df_ncm = pl.read_parquet(str(ncm_ref_path))
                    # Busca a posição normalizando a coluna Posicao
                    pos_row = df_ncm.filter(pl.col("Posicao").str.replace_all(r"[^0-9]", "") == ncm_pos_query).head(1)
                    if not pos_row.is_empty():
                        descr_pos_ncm = pos_row.row(0, named=True).get("Descr_Posicao", "")
            except:
                pass
        
        # Formatação Descrição: Segmento na linha 1; Descrição na linha 2; NCMs na linha 3
        ncm_info = f"{ncm_associado} ({descr_pos_ncm})" if descr_pos_ncm else ncm_associado
        full_desc = f"{seg_formatado}\nDescrição: {descricoes[0] if descricoes else ''}\nNCMs: {ncm_info}"
        
        return {
            "success": True,
            "data": {
                "codigo": codigo,
                "segmento": seg_formatado,
                "nome_segmento": segmento_nome,
                "descricoes": [full_desc],
                "ncms_associados": ncms
            }
        }
    except Exception as e:
        logger.error(f"[references] Erro CEST: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
