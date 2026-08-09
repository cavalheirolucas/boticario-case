import logging
import pandas as pd


logger = logging.getLogger()



#Caminho fícticio do arquivo de entrada, que será lido pela DAG.
DIRETORIO_ENTRADA = "/data/cobranca/entrada"
NOME_ARQUIVO = "pagamentos_d-1.csv"
CAMINHO_ARQUIVO = f"{DIRETORIO_ENTRADA}/{NOME_ARQUIVO}"

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
    df.loc[data_invalida, "motivo_validacao"] += "data_pagamento ausente ou invalida, "
    
    data_execucao = context["logical_date"].date()
    data_no_futuro = df["data_pagamento"].notna() & (df["data_pagamento"].dt.date > data_execucao)
    df.loc[data_no_futuro, "motivo_validacao"] += "data_pagamento no futuro,"

    #validação do valor pago: não pode ser nulo, nem negativo
    df["valor_pago"] = pd.to_numeric(df["valor_pago"], errors="coerce")
    valor_invalido = df["valor_pago"].isna()
    df.loc[valor_invalido, "motivo_validacao"] += "valor_pago ausente ou invalido; "

    valor_negativo = df["valor_pago"].notna() & (df["valor_pago"] < 0)
    df.loc[valor_negativo, "motivo_validacao"] += "valor_pago negativo; "

    #validação de duplicidade: não pode haver mais de um pagamento para o mesmo contrato no mesmo dia
    duplicadas = df.duplicated(subset=["cpf_cliente", "id_contrato", "data_pagamento"])
    df.loc[duplicadas, "motivo_validacao"] += "pagamento duplicado; "

    #validação do CPF: não pode ter tamanho diferente de 11
    cpf_tamanho_errado = (
        df["cpf_cliente"].astype(str).str.replace(r"\D", "", regex=True).str.len() != 11
    )
    df.loc[cpf_tamanho_errado, "motivo_validacao"] += "cpf com formato estranho; "

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