from pathlib import Path
import logging
from logging_config import setup_logging
from utils.loader import carregar_arquivos
from utils.cleaner import limpar_dados, validar_colunas_esperadas
from utils.reporter import gerar_relatorio, salvar_observacoes_nos_arquivos

def main():
    setup_logging()
    logging.info("Iniciando automação de faturamento...")

    pasta_input = Path("data/input")
    pasta_output = Path("data/output")
    pasta_output.mkdir(parents=True, exist_ok=True)

    df = carregar_arquivos(pasta_input)
    if df is None or df.empty:
        logging.warning("Nenhum dado carregado. Verifique a pasta data/input.")
        return

    col_ok = validar_colunas_esperadas(df)
    if not col_ok:
        logging.error("Colunas esperadas ausentes. Verifique o arquivo de entrada.")
        return

    df_limpo = limpar_dados(df)

    caminho_relatorio = pasta_output / "relatorio_faturamento.xlsx"
    gerar_relatorio(df_limpo, str(caminho_relatorio))

    # SALVAR observações de volta nos arquivos de origem
    salvar_observacoes_nos_arquivos(df_limpo, str(pasta_input))

    logging.info(f"Processamento concluído. Relatório salvo em: {caminho_relatorio}")

if __name__ == "__main__":
    main()
