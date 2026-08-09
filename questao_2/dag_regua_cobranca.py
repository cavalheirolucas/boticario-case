import logging
import pandas as pd
import os
import shutil
from datetime import datetime
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow import DAG
from airflow.sensors.filesystem import FileSensor
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator

logger = logging.getLogger()



#Caminho fícticio do arquivo de entrada, que será lido pela DAG.
DIRETORIO_ENTRADA = "/data/cobranca/entrada"
DIRETORIO_PROCESSADOS = "/data/cobranca/processados"
DIRETORIO_LOG = "/data/cobranca/log_arquivado"
NOME_ARQUIVO = "pagamentos_d-1.csv"

CAMINHO_ARQUIVO = f"{DIRETORIO_ENTRADA}/{NOME_ARQUIVO}"
CAMINHO_LOG = f"{DIRETORIO_LOG}/{NOME_ARQUIVO}"

CONN_ID_DB_PRODUCAO = "postgres_cobranca_prd"

#Colunas fícticias relacionadas a dados de cobrança somente para exemplificar validação dos dados.
COLUNAS_ESPERADAS = {
    "cpf_cliente",
    "id_contrato",
    "data_pagamento",
    "data_vencimento",
    "valor_pago"
}


#Funções Python chamadas pelas tasks


def processar_arquivo(**context):

    df = pd.read_csv(CAMINHO_ARQUIVO)


    # --- erro estrutural
    if df.empty:
        raise ValueError(f"O arquivo {CAMINHO_ARQUIVO} está vazio.")

    colunas_faltando = COLUNAS_ESPERADAS - set(df.columns)
    if colunas_faltando:
        raise ValueError(f"O arquivo {CAMINHO_ARQUIVO} está faltando as colunas: {colunas_faltando}")



    # --- erro de linha
    df["motivo_validacao"] = ""


    #validação da data de pagamento: não pode ser nula, nem futura (em relação a data de execução da DAG)
    df['data_pagamento'] = pd.to_datetime(df['data_pagamento'], errors="coerce")

    data_invalida = df["data_pagamento"].isna()
    df.loc[data_invalida, "motivo_validacao"] += "data_pagamento ausente ou invalida| "
    
    data_execucao = context["logical_date"].date()
    data_no_futuro = df["data_pagamento"].notna() & (df["data_pagamento"].dt.date > data_execucao)
    df.loc[data_no_futuro, "motivo_validacao"] += "data_pagamento no futuro| "

    #validação do valor pago: não pode ser nulo, nem negativo
    df["valor_pago"] = pd.to_numeric(df["valor_pago"], errors="coerce")
    valor_invalido = df["valor_pago"].isna()
    df.loc[valor_invalido, "motivo_validacao"] += "valor_pago ausente ou invalido| "

    valor_negativo = df["valor_pago"].notna() & (df["valor_pago"] < 0)
    df.loc[valor_negativo, "motivo_validacao"] += "valor_pago negativo| "

    #validação de duplicidade: não pode haver mais de um pagamento para o mesmo contrato no mesmo dia
    duplicadas = df.duplicated(subset=["cpf_cliente", "id_contrato", "data_pagamento"])
    df.loc[duplicadas, "motivo_validacao"] += "pagamento duplicado| "

    #validação do CPF: não pode ter tamanho diferente de 11
    cpf_tamanho_errado = (
        df["cpf_cliente"].astype(str).str.replace(r"\D", "", regex=True).str.len() != 11
    )
    df.loc[cpf_tamanho_errado, "motivo_validacao"] += "cpf com formato estranho| "

    #Coluna de status de validação: "valido" ou "pendente"
    df["status_validacao"] = df["motivo_validacao"].apply(
        lambda motivo: "pendente" if motivo else "valido"
    )

    qtd_pendente = (df["status_validacao"] == "pendente").sum()
    qtd_valida = (df["status_validacao"] == "valido").sum()

    logger.info(
        "%s linha(s) validas de %s no total (%s marcadas como pendente).",
        qtd_valida,
        len(df),
        qtd_pendente,
    )

    CAMINHO_SAIDA = f"{DIRETORIO_PROCESSADOS}/pagamentos_validados_{data_execucao}.csv"
    os.makedirs(DIRETORIO_PROCESSADOS, exist_ok=True)
    df.to_csv(f"{CAMINHO_SAIDA}", index=False)
    logger.info("Arquivo de saída gravado em: %s", CAMINHO_SAIDA)

    return CAMINHO_SAIDA

    



def destino_arquivo(**context):

    data_execucao = context["logical_date"]
    dia_da_semana = data_execucao.weekday()  

    if dia_da_semana < 5:
        return 'carregar_banco'
    return 'arquivar_log'




def carregar_banco(**context):

    dados_processados = context['ti'].xcom_pull(task_ids=processar_arquivo)
    
    df = pd.read_csv(dados_processados)

    colunas = ["cpf_cliente","id_contrato","data_pagamento","data_vencimento","valor_pago"]
    registros = list(df[colunas].itertuples(index=False, name=None))

    hook = PostgresHook(postgres_conn_id=CONN_ID_DB_PRODUCAO)
    conn = hook.get_conn()

    cursor = conn.cursor()
    try:
        cursor.executemany(
            f"""
            INSERT INTO regua_cobranca
            (cpf_cliente, id_contrato, data_pagamento, data_vencimento, valor_pago)
            VALUES (%s, %s, %s, %s, %s)
            """,
            registros
        )
        logger.info("%s linha(s) carregada(s) no banco de producao.", len(registros))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    
def arquivar_log():

    logger.info("Fim de semana, gravando em %s", DIRETORIO_LOG)
    if os.path.exists(CAMINHO_ARQUIVO):
        shutil.copy(CAMINHO_ARQUIVO, CAMINHO_LOG)
    logger.info("Arquivado em %s", CAMINHO_LOG)



# Construção da DAG

DEFAULT_ARGS = {
    "owner":"time-cobranca",
    "retries":3
}

with DAG(
    dag_id = "dag_regua_cobranca",
    description = "Atualizacao diaria da regua de Cobranca a partir do aqruivo de pagamentos",
    default_args = DEFAULT_ARGS,
    schedule = "0 6 * * *",
    start_date = datetime(2026, 8, 9),
    catchup = False
) as dag:

    aguardar_arquivo = FileSensor(
        task_id="aguardar_arquivo_pagamentos",
        filepath=CAMINHO_ARQUIVO,
        poke_interval=300
    )

    processar = PythonOperator(
        task_id="processar_arquivo",
        python_callable=processar_arquivo
    )

    decidir = BranchPythonOperator(
            task_id="decidir_destino",
            python_callable=destino_arquivo
        )

    carregar = PythonOperator(
            task_id="carregar_banco",
            python_callable=carregar_banco
        )

    arquivar = PythonOperator(
            task_id="arquivar_log",
            python_callable=arquivar_log
        )

    fim = EmptyOperator(
        task_id = "fim_pipeline",
        trigger_rule="none_failed_min_one_success"
    )


    aguardar_arquivo >> processar >> decidir
    decidir >> carregar >> fim
    decidir >> arquivar >> fim