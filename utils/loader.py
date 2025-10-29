from pathlib import Path
import pandas as pd
from typing import Optional

# Colunas aceitas/esperadas (em português, sem espaços/acentos)
COLUNAS_ESPERADAS = [
    "id_fatura",
    "id_cliente",
    "nome_cliente",
    "data_emissao",
    "data_vencimento",
    "valor_base",
    "imposto",
    "valor_total",
    "moeda",
    "metodo_pagamento",
    "status",
    "codigo_departamento",
    "conta_analitica",
    "observacoes"
]

def _normalizar_colunas(cols):
    """Normaliza nomes de colunas: minusculas, sem acentos, trocando espaços por underscore."""
    new = []
    for c in cols:
        c2 = str(c).strip().lower().replace(" ", "_")
        # manter apenas caracteres ascii simples (remove acentos se houver)
        import unicodedata
        c2 = unicodedata.normalize("NFKD", c2).encode("ASCII", "ignore").decode()
        new.append(c2)
    return new

def carregar_arquivos(pasta: Path) -> Optional[pd.DataFrame]:
    """
    Carrega todos os arquivos CSV/XLSX da pasta e concatena em um DataFrame.
    Normaliza nomes de coluna para o formato usado no projeto.
    """
    if not pasta.exists():
        raise FileNotFoundError(f"Pasta {pasta} não encontrada.")

    dados = []
    for arquivo in sorted(pasta.iterdir()):
        if arquivo.is_file() and arquivo.suffix.lower() in [".csv", ".xls", ".xlsx"]:
            if arquivo.suffix.lower() == ".csv":
                df = pd.read_csv(arquivo)
            else:
                df = pd.read_excel(arquivo)
            # normalizar colunas
            df.columns = _normalizar_colunas(df.columns)
            dados.append(df)

    if not dados:
        return None

    df_all = pd.concat(dados, ignore_index=True)

    # tentar mapear colunas alternativas para nomes esperados (ex.: issue_date -> data_emissao)
    mapping = {}
    for expected in COLUNAS_ESPERADAS:
        if expected in df_all.columns:
            continue
        # heurísticas de mapeamento:
        for col in df_all.columns:
            if col.replace("_", "") == expected.replace("_", ""):
                mapping[col] = expected
            # english -> portuguese simple matches
            elif col in ["issue_date", "invoice_id", "client_id", "client_name", "total"]:
                if expected in ["data_emissao", "id_fatura", "id_cliente", "nome_cliente", "valor_total"]:
                    mapping[col] = expected
    if mapping:
        df_all = df_all.rename(columns=mapping)

    return df_all
