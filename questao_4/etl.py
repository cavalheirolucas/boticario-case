
import sqlite3
import logging
import pandas as pd

DB_PATH = "vendas.db"
VENDAS_CSV = "base_vendas_boticario.csv"
METAS_CSV = "tabela_metas_mensais_estados.csv"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def extract():
    vendas = pd.read_csv(VENDAS_CSV)
    metas = pd.read_csv(METAS_CSV)
    logger.info('Dados Extraídos.')
    return vendas, metas


def transform(vendas: pd.DataFrame) -> pd.DataFrame:
    df = vendas.copy()

    #Tratando nome das cidades
    CITY_FIX = {
    "Belo Horisonte": "Belo Horizonte",
    "BH": "Belo Horizonte",
    "Brasilia": "Brasília",
    "Rio de Janero" : "Rio de Janeiro",
    "Rio de Janeiro/RJ" : "Rio de Janeiro",
    "SP - São Paulo" : "São Paulo",
    "Sao Paolo" : "São Paulo",
    "Sâo Paulo" : "São Paulo"}

    df["Cidade"] = df["Cidade"].replace(CITY_FIX)

    # Inclusão de Valor_Unitario ausente pela média do próprio produto
    df["Valor_Unitario"] = df["Valor_Unitario"].fillna(
        df.groupby("Produto")["Valor_Unitario"].transform("mean")
    )

    #Identificação de possíveis erros de digitação relacionados a quantidade, quantidades muito alta e poucos casos aparecendo em todos os canais
    df["Flag_Outlier_Qtd"] = (df["Quantidade"] >= 100).astype(int)

    #Estruturação de colunas adicionais
    df["Data"] = pd.to_datetime(df["Data"])
    df["Ano"] = df["Data"].dt.year
    df["Mês"] = df["Data"].dt.month
    df["Data"] = df["Data"].dt.strftime("%Y-%m-%d %H:%M:%S")
    df["Receita"] = df["Quantidade"] * df["Valor_Unitario"]
    df["Custo"] = df["Quantidade"] * df["Custo_Unitario"]
    df["Margem"] = df["Receita"] - df["Custo"]

    logger.info('Dados Transformados.')



    return df

#Carregamento das tabelas no banco
def load(df: pd.DataFrame, metas: pd.DataFrame):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS vendas")
    cursor.execute("""
        CREATE TABLE vendas (
            id_venda TEXT,
            data TEXT,
            ano INTEGER,
            mes INTEGER,
            canal TEXT,
            tipo_pagamento TEXT,
            estado TEXT,
            cidade TEXT,
            produto TEXT,
            quantidade INTEGER,
            valor_unitario REAL,
            custo_unitario REAL,
            categoria_produto TEXT,
            id_parceiro TEXT,
            id_cliente TEXT,
            genero_cliente TEXT,
            data_nascimento_cliente TEXT,
            feedback_cliente TEXT,
            status_entrega TEXT,
            cupom_utilizado TEXT,
            flag_primeira_compra TEXT,
            flag_outlier_qtd INTEGER,
            receita REAL,
            custo REAL,
            margem REAL
        )
    """)

    cols = ['id_venda','data','ano','mes','canal','tipo_pagamento','estado','cidade','produto',
    'quantidade','valor_unitario','custo_unitario','categoria_produto','id_parceiro','id_cliente',
    'genero_cliente','data_nascimento_cliente','feedback_cliente','status_entrega','cupom_utilizado',
    'flag_primeira_compra','flag_outlier_qtd','receita','custo','margem']
    
  
   
    data = list(df.itertuples(index=False, name=None)) 
    col_names = ','.join(f'"{c}"' for c in cols)

    cursor.executemany(
        f"INSERT INTO vendas ({col_names}) VALUES ({','.join(['?'] * len(cols))})", data)

    cursor.execute("DROP TABLE IF EXISTS metas")
    cursor.execute("""
        CREATE TABLE metas (
            ano INTEGER,
            mes INTEGER,
            estado TEXT,
            meta_faturamento_mensal REAL
        )
    """)

    cols_metas = ["ano", "mes", "estado", "meta_faturamento_mensal"]
    data_metas = list(metas.itertuples(index=False, name=None)) 
    col_names_metas = ','.join(f'"{c}"' for c in cols_metas)

    cursor.executemany(
        f"INSERT INTO metas ({col_names_metas}) VALUES (?,?,?,?)",
        data_metas
    )
    logger.info('Dados Carregados.')
    conn.commit()
    conn.close()
    

#Orquestração da etl
def run():
    vendas, metas = extract()
    vendas = transform(vendas)
    load(vendas, metas)


if __name__ == "__main__":
    run()