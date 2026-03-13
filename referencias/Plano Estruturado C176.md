# **Plano Estruturado: Integração do Registo C176 no Unificador de Produtos**

## **1\. Objetivo**

Garantir que todos os itens presentes nas operações de Ressarcimento de ICMS-ST (Registo EFD C176) sejam devidamente mapeados e incluídos na Tabela Mestre de Produtos da auditoria (produtos\_agregados.parquet), preservando as otimizações de memória e processamento distribuído do Polars.

## **2\. Racional da Otimização (Predicate Pushdown & Unique)**

O Registo C176 pode conter múltiplas ocorrências do mesmo cod\_item (uma para cada documento fiscal de saída que gera direito a ressarcimento).

Para evitar uma explosão na cardinalidade (e consequente estouro de memória/RAM) durante o JOIN com o Registo 0200, o plano dita que a extração de códigos únicos (.unique()) ocorra **antes** do cruzamento descritivo.

## **3\. Passos de Implementação no Código**

**Arquivo Alvo:** sefin\_audit\_2/cruzamentos/produtos/produto\_unid.py

**Classe Alvo:** UnificadorProdutos

### **Passo 3.1: Criar o método processar\_efd\_c176**

Este método deve ser adicionado logo após o método processar\_efd\_c170. Ele será responsável por construir o plano de execução (*LazyFrame*) exclusivo para os dados do C176.

**Código a ser inserido:**

    def processar\_efd\_c176(self):  
        """  
        Integra os produtos do registo C176 (Ressarcimento de ICMS-ST).  
        Garante que os produtos alvo de pedido de restituição constem na base mestre.  
        """  
        lf\_c176 \= self.\_safe\_scan("c176")  
        lf\_0200 \= self.\_safe\_scan("reg\_0200")

        if lf\_c176 is not None and lf\_0200 is not None:  
            \# 1\. Extrair apenas códigos únicos do C176 ANTES do join para economizar RAM  
            lf\_c176\_unica \= (  
                lf\_c176.select(\["cod\_item"\])  
                .filter(pl.col("cod\_item").is\_not\_null())  
                .unique()  
            )

            \# 2\. Preparar o lado direito (0200) com os descritivos  
            lf\_0200\_unica \= (  
                lf\_0200.select(\["cod\_item", "descr\_item", "cod\_ncm", "cest", "cod\_barra"\])  
                .filter(pl.col("cod\_item").is\_not\_null())  
                .unique(subset=\["cod\_item"\], keep="any")  
            )

            \# 3\. Realizar o join unificado  
            joined \= lf\_c176\_unica.join(lf\_0200\_unica, on="cod\_item", how="left", coalesce=True)  
              
            \# 4\. Projetar as colunas no schema restrito de produtos e adicionar à lista Lazy  
            self.lazy\_frames.append(  
                joined.select(\[  
                    pl.col("cod\_item").alias("codigo"),  
                    pl.col("descr\_item").alias("descricao"),  
                    pl.lit(None).cast(pl.String).alias("descr\_compl\_c170"),  
                    pl.col("cod\_ncm").alias("ncm"),  
                    pl.col("cest").alias("cest"),  
                    pl.col("cod\_barra").alias("gtin"),  
                    pl.lit(None).cast(pl.Categorical).alias("unid"), \# Fallback  
                    pl.lit("C176+0200").alias("fonte")  
                \]).pipe(aplicar\_strict\_schema)  
            )

### **Passo 3.2: Invocar o método na orquestração (construir\_plano\_mestre)**

Dentro do mesmo arquivo, localize o método construir\_plano\_mestre(). É nele que os nós do grafo de execução do Polars são unidos. Adicione a chamada self.processar\_efd\_c176().

**Alteração:**

    def construir\_plano\_mestre(self) \-\> pl.LazyFrame:  
        self.processar\_bloco\_h()  
        self.processar\_efd\_c170()  
        self.processar\_efd\_c176() \# \<-- ADICIONAR ESTA LINHA AQUI  
        self.processar\_documentos\_fiscais()

        if not self.lazy\_frames:  
            raise ValueError("Nenhum dado encontrado nos arquivos base (Bloco H, C170, C176, NFe/NFCe)")  
          
        \# O resto do método permanece inalterado (pl.concat, etc)  
        \# ...

## **4\. Plano de Teste e Validação**

Após realizar a modificação no arquivo .py, siga as etapas de validação para garantir que não houve regressão de performance e que a lógica está sendo aplicada corretamente.

### **4.1. Rodar pipeline em um CNPJ de teste**

Escolha um CNPJ que você sabe que tem arquivos C176 gerados no Parquet.

No terminal, execute o pipeline de produtos (caso tenha um script isolado ou pela API local):

\# Exemplo se existir um runner CLI  
python \-m cruzamentos.produtos.produto\_unid\_ver \--cnpj "SEU\_CNPJ\_TESTE"

### **4.2. Inspeção do Parquet Gerado**

Abra o arquivo final gerado (/CNPJ/SEU\_CNPJ\_TESTE/arquivos\_parquet/produtos\_unificados\_unid\_SEU\_CNPJ\_TESTE.parquet) usando seu ParquetView.tsx no Frontend ou via script interativo Python.

**Verificações necessárias:**

1. **Coluna fonte**: Verifique se existe a string C176+0200 na contagem de origens. Em produtos que aparecem em vários lugares, a coluna lista\_fonte agora deve mostrar coisas como: C170+0200, NFe, C176+0200.  
2. **Duplicidade**: O agrupamento final groupby("codigo") na classe base precisa estar absorvendo corretamente as linhas do C176, garantindo que o número total de itens únicos no banco de dados master de produtos não estourou artificialmente.  
3. **Consumo de Memória**: Observe os logs de debug (debug\_logs.txt) para verificar o tempo de processamento. A inclusão do .unique() precoce deve garantir que o tempo de execução permaneça estável, não impactando a performance atual.