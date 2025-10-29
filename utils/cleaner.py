import pandas as pd
import logging

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

ALTA_ALERTA = 20000.0  # threshold padrão; pode ser lido do sheet config

def validar_colunas_esperadas(df: pd.DataFrame) -> bool:
    cols = set(df.columns)
    missing = [c for c in COLUNAS_REQUERIDAS if c not in cols]
    if missing:
        logging.error(f"Colunas faltando: {missing}")
        return False
    return True

def _adicionar_observacao(row, msg):
    if not row.get("observacoes"):
        return msg
    return f"{row.get('observacoes')} | {msg}"

def limpar_dados(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpa e padroniza o DataFrame e preenche 'observacoes':
    - remove linhas vazias
    - converte datas
    - converte valores para numeric
    - detecta alertas (negativo, zero, acima do limiar)
    - identifica duplicatas por id_fatura
    - registra ações executadas em 'observacoes'
    """
    df = df.copy()
    # remover linhas totalmente vazias
    df = df.dropna(how="all")

    # garantir colunas existam antes de operar
    # converter datas
    for dt_col in ["data_emissao", "data_vencimento"]:
        if dt_col in df.columns:
            before_na = df[dt_col].isna().sum()
            df[dt_col] = pd.to_datetime(df[dt_col], errors="coerce")
            after_na = df[dt_col].isna().sum()
            if after_na > before_na:
                # marca as linhas em que a data falhou ao converter
                mask = df[dt_col].isna()
                df.loc[mask, "observacoes"] = df.loc[mask].apply(
                    lambda r: _adicionar_observacao(r, f"Data '{dt_col}' inválida/convertida para NaT"), axis=1
                )

    # converter valores
    for v_col in ["valor_base", "imposto", "valor_total"]:
        if v_col in df.columns:
            # contar não-numéricos
            coerced = pd.to_numeric(df[v_col], errors="coerce")
            mask_invalid = coerced.isna() & (~df[v_col].isna())
            if mask_invalid.any():
                df.loc[mask_invalid, "observacoes"] = df.loc[mask_invalid].apply(
                    lambda r: _adicionar_observacao(r, f"'{v_col}' inválido -> convertido 0"), axis=1
                )
            df[v_col] = coerced.fillna(0.0)

    # padroniza status e metodo_pagamento (também registra mudança)
    if "status" in df.columns:
        df["status"] = df["status"].astype(str).str.strip()
        new = df["status"].str.title()
        changed = new != df["status"]
        if changed.any():
            df.loc[changed, "observacoes"] = df.loc[changed].apply(
                lambda r: _adicionar_observacao(r, f"Status padronizado ('{r['status']}' -> '{str(r['status']).title()}')"), axis=1
            )
        df["status"] = new

    if "metodo_pagamento" in df.columns:
        df["metodo_pagamento"] = df["metodo_pagamento"].astype(str).str.strip()
        new = df["metodo_pagamento"].str.title()
        changed = new != df["metodo_pagamento"]
        if changed.any():
            df.loc[changed, "observacoes"] = df.loc[changed].apply(
                lambda r: _adicionar_observacao(r, f"Metodo pagamento padronizado"), axis=1
            )
        df["metodo_pagamento"] = new

    # recalcula total esperável a partir de base + imposto e registra diferença relevante
    if {"valor_base", "imposto", "valor_total"}.issubset(df.columns):
        df["_valor_calculado"] = (df["valor_base"].astype(float) + df["imposto"].astype(float)).round(2)
        mask_diff = (df["_valor_calculado"] != df["valor_total"])
        if mask_diff.any():
            df.loc[mask_diff, "observacoes"] = df.loc[mask_diff].apply(
                lambda r: _adicionar_observacao(r, f"Valor_total difere do cálculo (calc={r['_valor_calculado']}, original={r['valor_total']})"), axis=1
            )
            # opcional: atualizar valor_total para calculado? aqui só documentamos, não alteramos por padrão.

    # criar coluna alerta (texto curto)
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

    # anotar observações relacionadas a alertas
    if "alerta" in df.columns:
        mask_neg = df["alerta"] == "Negativo"
        if mask_neg.any():
            df.loc[mask_neg, "observacoes"] = df.loc[mask_neg].apply(
                lambda r: _adicionar_observacao(r, "Detectado valor negativo"), axis=1
            )
        mask_zero = df["alerta"] == "Zero"
        if mask_zero.any():
            df.loc[mask_zero, "observacoes"] = df.loc[mask_zero].apply(
                lambda r: _adicionar_observacao(r, "Detectado valor zero"), axis=1
            )
        mask_high = df["alerta"] == "Acima do limite"
        if mask_high.any():
            df.loc[mask_high, "observacoes"] = df.loc[mask_high].apply(
                lambda r: _adicionar_observacao(r, f"Valor acima do limiar ({ALTA_ALERTA})"), axis=1
            )

    # marcar duplicatas por id_fatura
    if "id_fatura" in df.columns:
        duplicated_mask = df.duplicated(subset=["id_fatura"], keep=False)
        df["duplicata"] = duplicated_mask
        if duplicated_mask.any():
            df.loc[duplicated_mask, "observacoes"] = df.loc[duplicated_mask].apply(
                lambda r: _adicionar_observacao(r, "Duplicata detectada (id_fatura repetida)"), axis=1
            )

    # ordenar por data_emissao se disponível
    if "data_emissao" in df.columns:
        df = df.sort_values(by="data_emissao", na_position="last")

    # remover coluna auxiliar
    if "_valor_calculado" in df.columns:
        df = df.drop(columns=["_valor_calculado"])

    # logs de resumo
    total = len(df)
    n_err = (df["alerta"] != "OK").sum() if "alerta" in df.columns else 0
    logging.info(f"Linhas processadas: {total}; alertas: {n_err}")

    # garantir que 'observacoes' seja string
    df["observacoes"] = df["observacoes"].fillna("").astype(str)

    return df
