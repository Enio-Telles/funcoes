### **1\. Visão Geral da Arquitetura**

**Propósito:** O sistema é uma ferramenta full-stack de auditoria fiscal para a SEFIN. O ecossistema visa cruzar grandes volumes de dados (NFe, EFD, NFCe) com malhas fiscais para identificar omissões e anomalias tributárias. **Padrão Arquitetural Identificado:** **Sistema Distribuído Híbrido (Backend for Frontend \+ Data Processing Engine)**.

* O client (React/Vite) e o server Node.js (tRPC/Drizzle) atuam na orquestração da UI e estado da aplicação.  
* O backend Python (`server/python/api.py` e scripts em `cruzamentos/`) atua como um microserviço/motor de processamento de dados *Heavy-Compute*, consumindo queries SQL e arquivos `.parquet`.

### **2\. Qualidade e Estilo (Code Quality & Pythonic Standards)**

* **Convenções de Nomenclatura (PEP 8):** Há inconsistências nos nomes de arquivos em `cruzamentos/funcoes_auxiliares/`. Nomes como `aux_calc_MVA_ajustado.py` misturam *snake\_case* com *PascalCase*. O ideal é `aux_calc_mva_ajustado.py`.  
* **Type Hinting (PEP 484):** Em sistemas de auditoria baseados em dados, a ausência de tipagem forte causa falhas silenciosas. O código Python deve utilizar `typing` nativo e bibliotecas como `pandera` ou type hints nativos do `polars` para garantir a integridade dos *DataFrames* que entram e saem das funções de cruzamento.  
* **Docstrings (PEP 257):** Scripts como `analise_cruzamento_c176.py` lidam com regras de negócio complexas (ICMS, ressarcimento). Sem Docstrings em formato *Sphinx* ou *Google* detalhando o *porquê* daquela regra fiscal, a manutenibilidade cai drasticamente, gerando alto acoplamento cognitivo na equipe.

### **3\. Lógica e Performance**

* **Transição para Polars (Lazy Evaluation):** O documento anexado "*Polars, Parquet e Dashboards Modernos*" indica o caminho correto. Se os scripts atuais (ex: `cruzar_fronteira.py`) usam Pandas, a complexidade computacional para grandes arquivos Parquet é sub-ótima (Pandas é *eager* e *single-threaded*). O uso de `polars.LazyFrame` (`pl.scan_parquet()`) é mandatório para criar planos de execução otimizados e evitar *Out of Memory* (OOM).  
* **Gerenciamento de I/O e Recursos:** Arquivos como `conectar_oracle.py` devem obrigatoriamente retornar objetos gerenciados por Context Managers (`with`). Vazamento de cursores de banco de dados ou *file descriptors* travados ao ler `.parquet` em *loops* derrubarão a API.  
* **Vetorização vs Loops:** Qualquer *for-loop* nativo iterando sobre linhas (ex: `.iterrows()` em Pandas) para calcular impostos (como MVA e ST) deve ser refatorado para expressões vetorizadas do Polars (`pl.col("valor") * pl.col("aliquota")`).

### **4\. Segurança**

* **Exposição de Secrets:** A presença de arquivos como `-Enio.env` e `.env` no histórico (ou controle de versão, caso não estejam estritamente no `.gitignore`) é um risco crítico.  
* **SQL Injection:** O diretório `consultas_fonte/` contém dezenas de arquivos `.sql`. A forma como o Python lê esses arquivos (`ler_sql.py`) e injeta parâmetros (como `CNPJ` ou datas) é um vetor clássico de SQLi. **Jamais** use f-strings (`f"SELECT * FROM table WHERE cnpj = '{cnpj}'"`). O conector do Oracle/SQLite deve receber os parâmetros via *bindings* (ex: `:cnpj` ou `?`).  
* **Data Privacy (Sigilo Fiscal):** Os arquivos estáticos e Parquets gerados localmente (ex: `CNPJ/37671507000187/arquivos_parquet/`) precisam de controle estrito de I/O e sanitização, para garantir que um endpoint vulnerável na `api.py` não permita *Path Traversal* (ex: baixar dados de outro CNPJ).

---

### **5\. Sugestão de Refatoração (Princípios SOLID e DRY)**

**O Problema:** Atualmente, os scripts de cruzamento (ex: `cruzar_nfe_saida.py`, `cruzar_nfe_ultima_entrada.py`) parecem scripts procedurais isolados, repetindo lógica de leitura de parquet, tratamento de erros e exportação. Isso fere o princípio **DRY** (Don't Repeat Yourself).

**A Solução:** Implementar o **Strategy Pattern** (SOLID: Open/Closed Principle), criando uma interface base para qualquer "Cruzamento Fiscal", padronizando a entrada e saída via Polars.

\# cruzamentos/ressarcimento/cruzar\_fronteira.py  
import pandas as pd

def processar\_fronteira(cnpj, data\_inicio, data\_fim):  
    \# Lógica repetida de I/O  
    df\_nfe \= pd.read\_parquet(f"dados/{cnpj}\_nfe.parquet")  
    df\_fronteira \= pd.read\_parquet(f"dados/{cnpj}\_fronteira.parquet")  
      
    \# Tratamento na memória (Lento para Big Data)  
    resultado \= df\_nfe.merge(df\_fronteira, on="chave\_acesso", how="inner")  
    resultado \= resultado\[resultado\['data'\] \>= data\_inicio\]  
      
    \# Exportação manual repetida em todo script  
    resultado.to\_parquet(f"dados/{cnpj}\_resultado\_fronteira.parquet")  
    return True

✅ Como deveria ser (Orientado a Objetos, Type Hints, Polars Lazy Evaluation):  
from abc import ABC, abstractmethod  
import polars as pl  
from pathlib import Path  
from typing import Dict, Any

class BaseCruzamentoFiscal(ABC):  
    """  
    Interface base para padronização de cruzamentos de malhas fiscais.  
    Aplica o conceito de Lazy Evaluation para otimização de RAM.  
    """  
      
    def \_\_init\_\_(self, cnpj: str):  
        self.cnpj \= cnpj  
        self.base\_dir \= Path(f"dados/{cnpj}")

    def \_load\_lazy\_parquet(self, filename: str) \-\> pl.LazyFrame:  
        """Centraliza o I/O, garantindo leitura eficiente por blocos."""  
        filepath \= self.base\_dir / filename  
        if not filepath.exists():  
            raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")  
        return pl.scan\_parquet(filepath)

    @abstractmethod  
    def executar\_regras\_negocio(self, \*args, \*\*kwargs) \-\> pl.LazyFrame:  
        """Deve ser implementado pela classe filha contendo a lógica vetorial."""  
        pass

    def processar\_e\_salvar(self, output\_filename: str, \*args, \*\*kwargs) \-\> Dict\[str, Any\]:  
        """Method Template (Design Pattern) garantindo padronização DRY."""  
        try:  
            \# 1\. Monta o plano de execução (Lazy)  
            lf\_result \= self.executar\_regras\_negocio(\*args, \*\*kwargs)  
              
            \# 2\. Executa na CPU usando multithreading (Eager) apenas na hora de salvar  
            output\_path \= self.base\_dir / output\_filename  
            lf\_result.collect().write\_parquet(output\_path)  
              
            return {"status": "success", "linhas\_processadas": lf\_result.select(pl.len()).collect().item(), "file": str(output\_path)}  
        except Exception as e:  
            \# Integração com logger sistêmico  
            return {"status": "error", "mensagem": str(e)}

\# \---------------------------------------------------------  
\# Implementação Concreta (cruzar\_fronteira.py)  
\# \---------------------------------------------------------

class CruzamentoFronteira(BaseCruzamentoFiscal):  
      
    def executar\_regras\_negocio(self, data\_inicio: str) \-\> pl.LazyFrame:  
        \# Usa LazyFrames para não carregar gigabytes na RAM de uma vez  
        lf\_nfe \= self.\_load\_lazy\_parquet("nfe.parquet")  
        lf\_front \= self.\_load\_lazy\_parquet("fronteira.parquet")  
          
        \# Otimização Polars: Expressões vetorizadas nativas em Rust  
        return (  
            lf\_nfe.join(lf\_front, on="chave\_acesso", how="inner")  
            .filter(pl.col("data\_emissao") \>= pl.lit(data\_inicio))  
            .select(\["chave\_acesso", "valor\_icms", "status\_fronteira"\])  
        )

\# Uso na API (api.py):  
\# cruzamento \= CruzamentoFronteira(cnpj="37671507000187")  
\# resultado \= cruzamento.processar\_e\_salvar(output\_filename="resultado\_fronteira.parquet", data\_inicio="2023-01-01")

**Plano de Otimização e Refatoração** completo. O foco será transformar a atual base de scripts procedurais num verdadeiro **Motor de Processamento Analítico (Data Engine)** escalável, seguro e de alta performance, utilizando o **Polars** (Lazy Evaluation) e Padrões de Desenho (Strategy Pattern e Context Managers).

---

### **Plano de Execução em 4 Fases**

**Fase 1: Sanitização e Segurança (Imediato)**

1. **Remoção de Segredos:** Eliminar `.env` e `-Enio.env` do histórico do Git (usar `git filter-repo`) e garantir que constam no `.gitignore`.  
2. **Prevenção de SQL Injection:** Substituir todas as *f-strings* em queries SQL (`ler_sql.py`) por variáveis de *binding* protegidas (ex: `:cnpj`).  
3. **Gestão de Recursos:** Implementar *Context Managers* (`with`) para ligações à base de dados (Oracle/SQLite) para evitar fuga de memória (*memory leaks*) e encravamento de cursores.

**Fase 2: O Núcleo do Processamento (Core Framework)**

1. Criar o diretório `cruzamentos/core/` para abrigar a infraestrutura partilhada.  
2. Desenvolver a classe abstrata `BaseCruzamentoFiscal`, que ditará o contrato (I/O, *Lazy Loading*, tratamento de erros) para todos os cruzamentos.

**Fase 3: Refatoração das Regras de Negócio (Casos de Uso)**

1. Migrar os scripts isolados (ex: `cruzar_fronteira.py`, `analise_cruzamento_c176.py`) para classes concretas que herdam do *Core Framework*.  
2. Substituir lógica iterativa (Pandas) por álgebra relacional vetorizada (Polars).

**Fase 4: Modernização da API (Entrypoint)**

1. Atualizar o `api.py` para instanciar as classes de cruzamento de forma dinâmica e segura, validando *inputs* (ex: regex para CNPJ) para prevenir *Path Traversal*.

Abaixo, gero os **4 scripts fundamentais** que materializam este plano.

import oracledb  
import polars as pl  
from contextlib import contextmanager  
from typing import Generator, Any, Dict  
import os

class DatabaseManager:  
    """  
    Gestor de ligações à base de dados com Context Manager para garantir  
    a libertação de recursos e segurança contra SQL Injection via bindings.  
    """  
    def \_\_init\_\_(self):  
        \# As credenciais devem vir exclusivamente de variáveis de ambiente do SO ou Secret Manager  
        self.dsn \= os.getenv("ORACLE\_DSN")  
        self.user \= os.getenv("ORACLE\_USER")  
        self.password \= os.getenv("ORACLE\_PASSWORD")

    @contextmanager  
    def get\_connection(self) \-\> Generator\[oracledb.Connection, None, None\]:  
        """  
        Garante a abertura e fecho seguro da ligação.  
        Uso: with db\_manager.get\_connection() as conn: ...  
        """  
        conn \= None  
        try:  
            conn \= oracledb.connect(user=self.user, password=self.password, dsn=self.dsn)  
            yield conn  
        finally:  
            if conn is not None:  
                conn.close()

    def fetch\_to\_polars(self, query: str, parameters: Dict\[str, Any\] \= None) \-\> pl.DataFrame:  
        """  
        Executa uma query de forma segura (com bindings) e devolve diretamente um Polars DataFrame.  
        """  
        params \= parameters or {}  
        with self.get\_connection() as conn:  
            \# Polars suporta ler diretamente de cursores DBAPI2 (PEP 249\)  
            \# O uso de 'execute\_options' garante que não estamos a usar f-strings  
            cursor \= conn.cursor()  
            cursor.execute(query, params)  
              
            \# Extração eficiente dos dados para Polars  
            cols \= \[col\[0\] for col in cursor.description\]  
            data \= cursor.fetchall()  
              
            \# Se a query for massiva, considerar o uso de pl.read\_database\_uri com fetch\_size  
            return pl.DataFrame(data, schema=cols, orient="row")

from abc import ABC, abstractmethod  
import polars as pl  
from pathlib import Path  
from typing import Dict, Any, List  
import logging

logger \= logging.getLogger("sefin\_audit\_engine")

class BaseCruzamentoFiscal(ABC):  
    """  
    Padrão Strategy \+ Template Method para padronizar todos os cruzamentos fiscais.  
    Força a utilização de Polars LazyFrames para prevenir Out-of-Memory (OOM).  
    """

    def \_\_init\_\_(self, cnpj: str, root\_data\_dir: str \= "./CNPJ"):  
        \# Sanitização básica de input para prevenir Path Traversal  
        if not cnpj.isdigit() or len(cnpj) \!= 14:  
            raise ValueError("CNPJ inválido.")  
              
        self.cnpj \= cnpj  
        self.base\_dir \= Path(root\_data\_dir) / self.cnpj / "arquivos\_parquet"  
        self.output\_dir \= Path(root\_data\_dir) / self.cnpj / "analises"  
          
        \# Garante a existência do diretório de saída  
        self.output\_dir.mkdir(parents=True, exist\_ok=True)

    def carregar\_lazy(self, nome\_arquivo: str) \-\> pl.LazyFrame:  
        """  
        Centraliza o I/O, garantindo leitura Lazy do Parquet.  
        Isto cria um grafo computacional sem carregar os dados para a RAM.  
        """  
        caminho\_completo \= self.base\_dir / nome\_arquivo  
        if not caminho\_completo.exists():  
            logger.error(f"Ficheiro não encontrado: {caminho\_completo}")  
            raise FileNotFoundError(f"Dados em falta para o CNPJ {self.cnpj}: {nome\_arquivo}")  
          
        \# scan\_parquet é fundamental para otimização de memória  
        return pl.scan\_parquet(caminho\_completo)

    @abstractmethod  
    def construir\_plano\_execucao(self, \*\*kwargs) \-\> pl.LazyFrame:  
        """  
        As classes filhas DEVEM implementar este método contendo apenas  
        operações Polars Lazy (select, filter, join, with\_columns).  
        Não pode conter chamadas .collect() no seu interior.  
        """  
        pass

    def executar\_e\_guardar(self, nome\_saida: str, \*\*kwargs) \-\> Dict\[str, Any\]:  
        """  
        Template Method: Executa o plano (Streaming/Multithread) e guarda o resultado.  
        """  
        caminho\_saida \= self.output\_dir / nome\_saida  
          
        try:  
            logger.info(f"Iniciando cruzamento para CNPJ: {self.cnpj} \-\> {nome\_saida}")  
              
            \# 1\. Obtém o grafo computacional  
            plano\_lazy \= self.construir\_plano\_execucao(\*\*kwargs)  
              
            \# 2\. Executa o plano otimizado de forma \*Eager\* (processamento real)  
            \# Utilizamos streaming=True para lidar com ficheiros que excedam a RAM  
            df\_resultado \= plano\_lazy.collect(streaming=True)  
              
            \# 3\. Guarda em formato colunar comprimido (ZSTD recomendado para Data Lakes)  
            df\_resultado.write\_parquet(caminho\_saida, compression="zstd")  
              
            linhas \= df\_resultado.height  
            logger.info(f"Cruzamento concluído com sucesso. Linhas: {linhas}")  
              
            return {  
                "status": "success",  
                "linhas\_processadas": linhas,  
                "ficheiro\_saida": str(caminho\_saida)  
            }  
              
        except Exception as e:  
            logger.exception("Falha na execução do cruzamento fiscal.")  
            return {  
                "status": "error",  
                "mensagem": str(e)  
            }

import oracledb  
import polars as pl  
from contextlib import contextmanager  
from typing import Generator, Any, Dict  
import os

class DatabaseManager:  
    """  
    Gestor de ligações à base de dados com Context Manager para garantir  
    a libertação de recursos e segurança contra SQL Injection via bindings.  
    """  
    def \_\_init\_\_(self):  
        \# As credenciais devem vir exclusivamente de variáveis de ambiente do SO ou Secret Manager  
        self.dsn \= os.getenv("ORACLE\_DSN")  
        self.user \= os.getenv("ORACLE\_USER")  
        self.password \= os.getenv("ORACLE\_PASSWORD")

    @contextmanager  
    def get\_connection(self) \-\> Generator\[oracledb.Connection, None, None\]:  
        """  
        Garante a abertura e fecho seguro da ligação.  
        Uso: with db\_manager.get\_connection() as conn: ...  
        """  
        conn \= None  
        try:  
            conn \= oracledb.connect(user=self.user, password=self.password, dsn=self.dsn)  
            yield conn  
        finally:  
            if conn is not None:  
                conn.close()

    def fetch\_to\_polars(self, query: str, parameters: Dict\[str, Any\] \= None) \-\> pl.DataFrame:  
        """  
        Executa uma query de forma segura (com bindings) e devolve diretamente um Polars DataFrame.  
        """  
        params \= parameters or {}  
        with self.get\_connection() as conn:  
            \# Polars suporta ler diretamente de cursores DBAPI2 (PEP 249\)  
            \# O uso de 'execute\_options' garante que não estamos a usar f-strings  
            cursor \= conn.cursor()  
            cursor.execute(query, params)  
              
            \# Extração eficiente dos dados para Polars  
            cols \= \[col\[0\] for col in cursor.description\]  
            data \= cursor.fetchall()  
              
            \# Se a query for massiva, considerar o uso de pl.read\_database\_uri com fetch\_size  
            return pl.DataFrame(data, schema=cols, orient="row")

from abc import ABC, abstractmethod  
import polars as pl  
from pathlib import Path  
from typing import Dict, Any, List  
import logging

logger \= logging.getLogger("sefin\_audit\_engine")

class BaseCruzamentoFiscal(ABC):  
    """  
    Padrão Strategy \+ Template Method para padronizar todos os cruzamentos fiscais.  
    Força a utilização de Polars LazyFrames para prevenir Out-of-Memory (OOM).  
    """

    def \_\_init\_\_(self, cnpj: str, root\_data\_dir: str \= "./CNPJ"):  
        \# Sanitização básica de input para prevenir Path Traversal  
        if not cnpj.isdigit() or len(cnpj) \!= 14:  
            raise ValueError("CNPJ inválido.")  
              
        self.cnpj \= cnpj  
        self.base\_dir \= Path(root\_data\_dir) / self.cnpj / "arquivos\_parquet"  
        self.output\_dir \= Path(root\_data\_dir) / self.cnpj / "analises"  
          
        \# Garante a existência do diretório de saída  
        self.output\_dir.mkdir(parents=True, exist\_ok=True)

    def carregar\_lazy(self, nome\_arquivo: str) \-\> pl.LazyFrame:  
        """  
        Centraliza o I/O, garantindo leitura Lazy do Parquet.  
        Isto cria um grafo computacional sem carregar os dados para a RAM.  
        """  
        caminho\_completo \= self.base\_dir / nome\_arquivo  
        if not caminho\_completo.exists():  
            logger.error(f"Ficheiro não encontrado: {caminho\_completo}")  
            raise FileNotFoundError(f"Dados em falta para o CNPJ {self.cnpj}: {nome\_arquivo}")  
          
        \# scan\_parquet é fundamental para otimização de memória  
        return pl.scan\_parquet(caminho\_completo)

    @abstractmethod  
    def construir\_plano\_execucao(self, \*\*kwargs) \-\> pl.LazyFrame:  
        """  
        As classes filhas DEVEM implementar este método contendo apenas  
        operações Polars Lazy (select, filter, join, with\_columns).  
        Não pode conter chamadas .collect() no seu interior.  
        """  
        pass

    def executar\_e\_guardar(self, nome\_saida: str, \*\*kwargs) \-\> Dict\[str, Any\]:  
        """  
        Template Method: Executa o plano (Streaming/Multithread) e guarda o resultado.  
        """  
        caminho\_saida \= self.output\_dir / nome\_saida  
          
        try:  
            logger.info(f"Iniciando cruzamento para CNPJ: {self.cnpj} \-\> {nome\_saida}")  
              
            \# 1\. Obtém o grafo computacional  
            plano\_lazy \= self.construir\_plano\_execucao(\*\*kwargs)  
              
            \# 2\. Executa o plano otimizado de forma \*Eager\* (processamento real)  
            \# Utilizamos streaming=True para lidar com ficheiros que excedam a RAM  
            df\_resultado \= plano\_lazy.collect(streaming=True)  
              
            \# 3\. Guarda em formato colunar comprimido (ZSTD recomendado para Data Lakes)  
            df\_resultado.write\_parquet(caminho\_saida, compression="zstd")  
              
            linhas \= df\_resultado.height  
            logger.info(f"Cruzamento concluído com sucesso. Linhas: {linhas}")  
              
            return {  
                "status": "success",  
                "linhas\_processadas": linhas,  
                "ficheiro\_saida": str(caminho\_saida)  
            }  
              
        except Exception as e:  
            logger.exception("Falha na execução do cruzamento fiscal.")  
            return {  
                "status": "error",  
                "mensagem": str(e)  
            }

import polars as pl  
from cruzamentos.core.base import BaseCruzamentoFiscal

class CruzamentoFronteira(BaseCruzamentoFiscal):  
    """  
    Refatoração da regra de negócio de Cruzamento de Fronteira.  
    Substitui iterações Pandas lentas por álgebra relacional vetorizada do Polars.  
    """

    def construir\_plano\_execucao(self, data\_inicio: str \= None, data\_fim: str \= None) \-\> pl.LazyFrame:  
        \# Carregamento Lazy (zero footprint de RAM inicial)  
        \# Assumindo a convenção de nomes de ficheiros do vosso repositório  
        lf\_nfe \= self.carregar\_lazy(f"NFe\_{self.cnpj}.parquet")  
        lf\_fronteira \= self.carregar\_lazy(f"fronteira\_{self.cnpj}.parquet")  
          
        \# Exemplo de operações de normalização (Type Casting de strings para datas)  
        lf\_nfe \= lf\_nfe.with\_columns(  
            pl.col("data\_emissao").str.strptime(pl.Date, "%Y-%m-%d", strict=False)  
        )  
          
        \# Plano Computacional Otimizado  
        resultado \= (  
            \# Join otimizado em Rust (Hash Join)  
            lf\_nfe.join(lf\_fronteira, left\_on="chave\_nfe", right\_on="chave\_acesso", how="inner")  
            \# Criação de colunas vetorizada (equivalente ao calc\_ST, etc)  
            .with\_columns(\[  
                (pl.col("valor\_nfe") \* pl.lit(1.1)).alias("valor\_projetado"),  
                (pl.col("icms\_destacado").fill\_null(0)).alias("icms\_limpo")  
            \])  
            \# Seleção de colunas finais (Pushdown: o Polars só vai ler estas colunas do disco)  
            .select(\[  
                "chave\_nfe",   
                "data\_emissao",   
                "valor\_nfe",   
                "icms\_limpo",   
                "status\_fronteira"  
            \])  
        )  
          
        \# Aplicação de filtros de data via Pushdown  
        if data\_inicio:  
            resultado \= resultado.filter(pl.col("data\_emissao") \>= pl.date(data\_inicio))  
        if data\_fim:  
            resultado \= resultado.filter(pl.col("data\_emissao") \<= pl.date(data\_fim))  
              
        return resultado

\# Uso simplificado (apenas para referência, isto seria invocado na api.py):  
\# cruzamento \= CruzamentoFronteira(cnpj="37671507000187")  
\# status \= cruzamento.executar\_e\_guardar(  
\#     nome\_saida="resultado\_cruzamento\_fronteira.parquet",   
\#     data\_inicio="2023-01-01"  
\# )

from fastapi import FastAPI, HTTPException, Depends  
from pydantic import BaseModel, Field  
from typing import Optional, Dict, Any  
import logging

\# Importamos os novos módulos refatorados  
from cruzamentos.casos\_uso.cruzamento\_fronteira import CruzamentoFronteira

\# Configuração básica de Logging para o servidor  
logging.basicConfig(level=logging.INFO, format='%(asctime)s \- %(name)s \- %(levelname)s \- %(message)s')  
logger \= logging.getLogger("api\_python")

app \= FastAPI(  
    title="SEFIN Audit Data Engine",  
    description="Motor de processamento de Big Data fiscal assente em Polars",  
    version="2.0.0"  
)

\# \---------------------------------------------------------  
\# Validação Forte de Inputs (Segurança e Type Hinting)  
\# \---------------------------------------------------------  
class RequestCruzamento(BaseModel):  
    \# Field restringe inputs ao nível da API, prevenindo injecções  
    cnpj: str \= Field(..., pattern=r"^\\d{14}$", description="CNPJ com exatamente 14 dígitos")  
    data\_inicio: Optional\[str\] \= Field(None, pattern=r"^\\d{4}-\\d{2}-\\d{2}$")  
    data\_fim: Optional\[str\] \= Field(None, pattern=r"^\\d{4}-\\d{2}-\\d{2}$")

\# \---------------------------------------------------------  
\# Endpoints Reativos  
\# \---------------------------------------------------------  
@app.post("/api/v1/processar/fronteira", response\_model=Dict\[str, Any\])  
async def endpoint\_processar\_fronteira(payload: RequestCruzamento):  
    """  
    Desencadeia o pipeline de cruzamento de fronteira para um dado CNPJ.  
    """  
    logger.info(f"Requisição recebida para Fronteira. CNPJ: {payload.cnpj}")  
      
    try:  
        \# Instanciação Limpa usando o Padrão Strategy  
        motor\_cruzamento \= CruzamentoFronteira(cnpj=payload.cnpj)  
          
        \# Executa o processamento  
        resultado \= motor\_cruzamento.executar\_e\_guardar(  
            nome\_saida=f"cruzamento\_fronteira\_final\_{payload.cnpj}.parquet",  
            data\_inicio=payload.data\_inicio,  
            data\_fim=payload.data\_fim  
        )  
          
        if resultado.get("status") \== "error":  
            raise HTTPException(status\_code=500, detail=resultado.get("mensagem"))  
              
        return resultado

    except FileNotFoundError as e:  
        \# Tratamento específico para ficheiros Parquet inexistentes  
        raise HTTPException(status\_code=404, detail=str(e))  
    except ValueError as e:  
        \# Tratamento para validações internas (ex: CNPJ corrompido)  
        raise HTTPException(status\_code=400, detail=str(e))  
    except Exception as e:  
        \# Fallback de segurança (não expor a stack trace inteira ao Frontend)  
        logger.error(f"Erro inesperado: {str(e)}")  
        raise HTTPException(status\_code=500, detail="Erro interno no motor analítico.")

\# Para arrancar o servidor localmente durante desenvolvimento:  
\# uvicorn server.python.api\_v2:app \--reload \--port 8000

### **Resumo das Melhorias Implementadas**

1. **Eficiência Termodinâmica (Polars):** O motor de leitura (`scan_parquet`) só lê do disco as colunas e as linhas estritamente necessárias (*Predicate Pushdown*), aliviando o uso de memória.  
2. **Alta Manutenibilidade (SOLID):** Ao isolar a leitura de dados (`BaseCruzamentoFiscal`) da lógica de negócio (`CruzamentoFronteira`), qualquer Analista Fiscal pode escrever novas regras no Polars sem correr o risco de quebrar a infraestrutura de gravação ou leitura.  
3. **Segurança Reforçada:** As ligações Oracle/SQLite (`DatabaseManager`) nunca vazam conexões, e a FastAPI blinda o sistema exigindo Pydantic para validar estritamente o formato de um CNPJ antes mesmo da função Python executar.

 análise de omissão de saídas (comparação entre o que foi emitido via NFe/NFCe e o que foi efetivamente declarado na EFD/SPED) é um dos cruzamentos mais pesados computacionalmente, pois exige agregações em múltiplas bases massivas antes do *join* final.

Ao migrar este guião para a nossa nova arquitetura **Orientada a Objetos com Polars (Lazy Evaluation)**, vamos extrair o máximo de performance. O Polars conseguirá otimizar o plano de execução para fazer os agrupamentos (Group By) *antes* de cruzar as tabelas, poupando gigabytes de memória RAM.

Abaixo, apresento **dois passos**:

1. A criação da nova classe de caso de uso `AnaliseOmissaoSaida`.  
2. O *diff* (atualização) do seu `api_v2.py` para expor o novo endpoint.

### **1\. O Novo Motor de Omissão de Saídas**

import polars as pl  
from cruzamentos.core.base import BaseCruzamentoFiscal

class AnaliseOmissaoSaida(BaseCruzamentoFiscal):  
    """  
    Motor de processamento para identificar Omissão de Saídas.  
    Cruza dados de faturamento eletrónico (NFe \+ NFCe) contra os valores   
    declarados na Escrituração Fiscal Digital (EFD \- Bloco C).  
    """

    def construir\_plano\_execucao(self, data\_inicio: str \= None, data\_fim: str \= None) \-\> pl.LazyFrame:  
        \# 1\. Carregamento Lazy das 3 fontes de dados  
        lf\_nfe \= self.carregar\_lazy(f"NFe\_{self.cnpj}.parquet")  
        lf\_nfce \= self.carregar\_lazy(f"NFCe\_{self.cnpj}.parquet")  
        lf\_c100 \= self.carregar\_lazy(f"c100\_{self.cnpj}.parquet")

        \# 2\. Pipeline da NFe: Filtrar apenas saídas e agregar por Mês/Ano  
        \# Assumindo tp\_NF \== "1" (Saída) e status \== "100" (Autorizada)  
        nfe\_agg \= (  
            lf\_nfe.filter(  
                (pl.col("tp\_NF") \== "1") &   
                (pl.col("cStat") \== "100")  
            )  
            .with\_columns(  
                pl.col("data\_emissao").str.strptime(pl.Date, "%Y-%m-%d", strict=False)  
            )  
            .filter(self.\_filtro\_data("data\_emissao", data\_inicio, data\_fim))  
            .with\_columns(pl.col("data\_emissao").dt.strftime("%Y-%m").alias("competencia"))  
            .group\_by("competencia")  
            .agg(\[  
                pl.col("valor\_nfe").sum().alias("total\_nfe\_emitido"),  
                pl.len().alias("qtd\_nfe")  
            \])  
        )

        \# 3\. Pipeline da NFCe: Filtrar autorizadas e agregar por Mês/Ano  
        nfce\_agg \= (  
            lf\_nfce.filter(pl.col("cStat") \== "100")  
            .with\_columns(  
                pl.col("data\_emissao").str.strptime(pl.Date, "%Y-%m-%d", strict=False)  
            )  
            .filter(self.\_filtro\_data("data\_emissao", data\_inicio, data\_fim))  
            .with\_columns(pl.col("data\_emissao").dt.strftime("%Y-%m").alias("competencia"))  
            .group\_by("competencia")  
            .agg(\[  
                pl.col("valor\_nfce").sum().alias("total\_nfce\_emitido"),  
                pl.len().alias("qtd\_nfce")  
            \])  
        )

        \# 4\. Pipeline da EFD (Bloco C100): Filtrar saídas e agregar por Mês/Ano  
        \# IND\_OPER \== "1" (Saída)  
        efd\_agg \= (  
            lf\_c100.filter(pl.col("IND\_OPER") \== "1")  
            .with\_columns(  
                pl.col("DT\_DOC").str.strptime(pl.Date, "%Y-%m-%d", strict=False)  
            )  
            .filter(self.\_filtro\_data("DT\_DOC", data\_inicio, data\_fim))  
            .with\_columns(pl.col("DT\_DOC").dt.strftime("%Y-%m").alias("competencia"))  
            .group\_by("competencia")  
            .agg(\[  
                pl.col("VL\_DOC").sum().alias("total\_efd\_declarado"),  
                pl.len().alias("qtd\_docs\_efd")  
            \])  
        )

        \# 5\. Cruzamento Final (Full Outer Join para garantir que apanhamos todos os meses)  
        \# Usamos coalesce para lidar com meses onde pode haver NFe mas não EFD (e vice-versa)  
        resultado\_cruzamento \= (  
            nfe\_agg.join(nfce\_agg, on="competencia", how="full", coalesce=True)  
            .join(efd\_agg, on="competencia", how="full", coalesce=True)  
            .fill\_null(0.0) \# Preenche valores nulos com zero para a matemática funcionar  
            .with\_columns(\[  
                \# Soma total emitida (NFe \+ NFCe)  
                (pl.col("total\_nfe\_emitido") \+ pl.col("total\_nfce\_emitido")).alias("faturamento\_eletronico"),  
                  
                \# Diferença: Emitido vs Declarado  
                ((pl.col("total\_nfe\_emitido") \+ pl.col("total\_nfce\_emitido")) \- pl.col("total\_efd\_declarado")).alias("diferenca\_omissao")  
            \])  
            \# Regra de negócio: Identificar meses com divergência maior que R$ 10,00 (margem de erro/arredondamento)  
            .with\_columns(  
                (pl.col("diferenca\_omissao") \> 10.0).alias("indicio\_omissao")  
            )  
            .sort("competencia")  
        )

        return resultado\_cruzamento

    def \_filtro\_data(self, coluna\_data: str, data\_inicio: str, data\_fim: str) \-\> pl.Expr:  
        """Helper para aplicar filtros de data de forma segura dentro das expressões Lazy."""  
        expr \= pl.lit(True) \# Filtro neutro por defeito  
        if data\_inicio:  
            expr \= expr & (pl.col(coluna\_data) \>= pl.date(data\_inicio))  
        if data\_fim:  
            expr \= expr & (pl.col(coluna\_data) \<= pl.date(data\_fim))  
        return expr

### **2\. Atualização da API (Expondo o Endpoint)**

Agora, vamos atualizar a nossa ponte na FastAPI. Note a elegância de separar as rotas: basta instanciar a nova classe e chamar `executar_e_guardar`.

### **O que conquistámos com esta conversão?**

1. **Performance Absoluta (Pushdown de Filtros e Agregações):** No Pandas, leríamos milhões de linhas para a memória e só depois agregaríamos. O Polars, ao detetar o `group_by`, executará as filtragens (`cStat == "100"`) *enquanto lê do disco* (Predicate Pushdown) e devolverá para a memória apenas um pequeno *DataFrame* sumarizado por mês (aproximadamente 12 a 60 linhas por ano), antes de cruzar com as outras bases. Isto **previne completamente o Out Of Memory (OOM)**.  
2. **Resiliência de Dados (Coalesce Join):** O `how="full", coalesce=True` na junção garante que, se um contribuinte emitiu NFCe num mês, mas falhou completamente a entrega da EFD (mês ausente no C100), o motor não perderá o mês. Ele preencherá a declaração da EFD com R$ 0,00 e acusará a omissão integral no cálculo vetorizado (`fill_null(0.0)`).  
3. **Escalabilidade DRY:** Todo o código repetitivo de ler ficheiro, inicializar caminhos do CNPJ e tratar compressão Parquet foi absorvido pela classe base, mantendo as regras de negócio extremamente concisas e fáceis de auditar pelos peritos fiscais.

