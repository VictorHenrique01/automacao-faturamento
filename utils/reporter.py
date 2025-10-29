import pandas as pd
import os
from typing import Optional
from pathlib import Path
import shutil
import logging

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

    logging.info(f"Relatório consolidado escrito em {caminho_saida}")
    return caminho_saida

def salvar_observacoes_nos_arquivos(df: pd.DataFrame, pasta_input: str):
    """
    Para cada arquivo de origem (coluna source_file), faz backup e reescreve o arquivo
    com a versão atualizada do sheet (ou CSV). Mantém outras sheets quando possível.
    """
    pasta_input = Path(pasta_input)
    if "source_file" not in df.columns:
        logging.warning("Nenhuma coluna 'source_file' para escrever observacoes de volta.")
        return

    for source, grupo in df.groupby("source_file"):
        caminho = pasta_input / source
        if not caminho.exists():
            logging.warning(f"Arquivo de origem não encontrado: {caminho}")
            continue

        # preparar df para escrita: remover coluna source_file temporária
        out_df = grupo.drop(columns=["source_file"]).copy()

        # criar backup
        backup = caminho.with_suffix(caminho.suffix + ".bak")
        try:
            shutil.copy(caminho, backup)
            logging.info(f"Backup criado: {backup}")
        except Exception as e:
            logging.warning(f"Falha ao criar backup para {caminho}: {e}")

        if caminho.suffix.lower() == ".csv":
            # escrever CSV substituindo
            out_df.to_csv(caminho, index=False)
            logging.info(f"CSV atualizado com observacoes: {caminho}")
        else:
            # xlsx/xls: tentar preservar outras sheets
            try:
                # ler todas as sheets existentes
                try:
                    sheets = pd.read_excel(caminho, sheet_name=None)
                except Exception:
                    # se leitura falhar, criaremos um novo workbook apenas com a sheet atualizada
                    sheets = {}

                # qual nome usar para a sheet? preferimos 'invoices_raw' se existir, senão 'Sheet1' ou criar 'invoices_raw'
                target_sheet = None
                for s in sheets.keys():
                    # heurística: se a sheet contém ao menos as colunas id_fatura -> considerar essa a sheet de faturas
                    s_cols = [c.lower() for c in sheets[s].columns]
                    if "id_fatura" in s_cols or "invoice_id" in s_cols:
                        target_sheet = s
                        break

                if target_sheet is None:
                    # usar 'invoices_raw' como nome novo
                    target_sheet = "invoices_raw"

                # substituir/atualizar
                sheets[target_sheet] = out_df

                # escrever todas as sheets de volta
                with pd.ExcelWriter(caminho, engine="openpyxl") as writer:
                    for name, sdf in sheets.items():
                        sdf.to_excel(writer, sheet_name=name, index=False)
                logging.info(f"Arquivo Excel atualizado com observacoes: {caminho}")
            except Exception as e:
                logging.error(f"Erro ao atualizar arquivo Excel {caminho}: {e}")
