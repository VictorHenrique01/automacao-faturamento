import pandas as pd
import logging
from typing import List

COLUNAS_REQUERIDAS = [
    "id_fatura",
    "id_cliente",
    "nome_cliente",
    "data_emissao",
    "data_vencimento",
    "valor_base",
    "imposto",
    "valor_total"
]

ALTA_ALERTA = 20000.0  # threshold default; você pode ler de config se quiser

def validar_colunas_esperadas(df: pd.DataFrame) -> bool:
    cols = set(df.columns)
    missing = [c for c in COLUNAS_REQUERIDAS if c not in cols]
    if missing:
        logging.error(f"Colunas faltando: {missing}")
        return False
    return True

def limpar_dados(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpa e padroniza o DataFrame:
    - remove linhas vazias
    - converte datas
    - converte valores para numeric
    - detecta alertas (negativo, zero, acima do limiar)
    - remove duplicatas exatas por id_fatura
    """
    df = df.copy()
    # remover linhas totalmente vazias
    df = df.dropna(how="all")

    # garantir colunas existam antes de operar
    # converter datas
    for dt_col in ["data_emissao", "data_vencimento"]:
        if dt_col in df.columns:
            df[dt_col] = pd.to_datetime(df[dt_col], errors="coerce")

    # converter valores
    for v_col in ["valor_base", "imposto", "valor_total"]:
        if v_col in df.columns:
            df[v_col] = pd.to_numeric(df[v_col], errors="coerce").fillna(0.0)

    # padroniza status e metodo_pagamento
    if "status" in df.columns:
        df["status"] = df["status"].astype(str).str.strip().str.title()

    if "metodo_pagamento" in df.columns:
        df["metodo_pagamento"] = df["metodo_pagamento"].astype(str).str.strip().str.title()

    # criar coluna alerta
    def alerta_row(row):
        val = row.get("valor_total", 0.0)
        if pd.isna(val):
            return "Valor inválido"
        if val < 0:
            return "Negativo"
        if val == 0:
            return "Zero"
        if val > ALTA_ALERTA:
            return "Acima do limite"
        return "OK"

    df["alerta"] = df.apply(alerta_row, axis=1)

    # marcar duplicatas por id_fatura
    if "id_fatura" in df.columns:
        duplicated_mask = df.duplicated(subset=["id_fatura"], keep=False)
        df["duplicata"] = duplicated_mask

    # ordenar por data_emissao se disponível
    if "data_emissao" in df.columns:
        df = df.sort_values(by="data_emissao", na_position="last")

    # logs de resumo
    total = len(df)
    n_err = (df["alerta"] != "OK").sum() if "alerta" in df.columns else 0
    logging.info(f"Linhas processadas: {total}; alertas: {n_err}")

    return df
