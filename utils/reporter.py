import pandas as pd
import os
from typing import Optional

def gerar_relatorio(df: pd.DataFrame, caminho_saida: str) -> str:
    """
    Gera um arquivo Excel com:
    - sheet 'dados_limpos' -> dataframe completo
    - sheet 'resumo_cliente' -> agregação por cliente
    - sheet 'alertas' -> linhas com alerta != OK
    """
    os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)

    # Agregar por cliente
    if "nome_cliente" in df.columns and "valor_total" in df.columns:
        resumo = (
            df.groupby("nome_cliente", as_index=False)
            .agg(
                total_faturado = ("valor_total", "sum"),
                qtd_documentos = ("id_fatura", "count"),
                media_fatura = ("valor_total", "mean")
            )
            .sort_values(by="total_faturado", ascending=False)
        )
    else:
        resumo = pd.DataFrame()

    alertas = df[df.get("alerta", "OK") != "OK"] if "alerta" in df.columns else pd.DataFrame()

    with pd.ExcelWriter(caminho_saida, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="dados_limpos", index=False)
        resumo.to_excel(writer, sheet_name="resumo_cliente", index=False)
        alertas.to_excel(writer, sheet_name="alertas", index=False)

    return caminho_saida
