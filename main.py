from pathlib import Path
import logging
from logging_config import setup_logging
from utils.loader import carregar_arquivos
from utils.cleaner import limpar_dados, validar_colunas_esperadas
from utils.reporter import gerar_relatorio
# from utils.emailer import enviar_relatorio  # descomente se quiser enviar por email

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

    # validar e/ou mapear colunas
    col_ok = validar_colunas_esperadas(df)
    if not col_ok:
        logging.error("Colunas esperadas ausentes. Verifique o arquivo de entrada.")
        return

    df_limpo = limpar_dados(df)

    caminho_relatorio = pasta_output / "relatorio_faturamento.xlsx"
    gerar_relatorio(df_limpo, str(caminho_relatorio))

    logging.info(f"Processamento concluído. Relatório salvo em: {caminho_relatorio}")

    # Opcional: enviar por email
    # enviar_relatorio(caminho_relatorio, destinatarios=["financeiro@exemplo.com"])

if __name__ == "__main__":
    main()
