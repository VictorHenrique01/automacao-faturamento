import os
import logging
import yagmail
from typing import List, Optional
from dotenv import load_dotenv

# =========================
# CONFIGURAÇÃO DO LOGGER
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S",
)
logger = logging.getLogger(__name__)

# =========================
# CARREGAR VARIÁVEIS DE AMBIENTE
# =========================
load_dotenv()

SMTP_USER = os.getenv("EMAIL_USER")
SMTP_PASS = os.getenv("EMAIL_PASS")


# =========================
# FUNÇÃO PRINCIPAL DE ENVIO
# =========================
def enviar_relatorio(
    caminho_arquivo: str,
    destinatarios: List[str],
    assunto: str = "Relatório de Faturamento",
    corpo: Optional[str] = None,
) -> bool:
    """
    Envia um e-mail com relatório em anexo.

    Args:
        caminho_arquivo (str): Caminho do arquivo Excel a ser enviado.
        destinatarios (List[str]): Lista de e-mails dos destinatários.
        assunto (str, opcional): Assunto do e-mail. Padrão: "Relatório de Faturamento".
        corpo (str, opcional): Corpo do e-mail em formato de texto ou HTML.
    
    Returns:
        bool: True se o envio for bem-sucedido, False caso contrário.
    """

    if not SMTP_USER or not SMTP_PASS:
        logger.error("Credenciais de e-mail ausentes. Configure EMAIL_USER e EMAIL_PASS no .env.")
        return False

    if not destinatarios:
        logger.error("Nenhum destinatário informado.")
        return False

    if not os.path.exists(caminho_arquivo):
        logger.error(f"Arquivo não encontrado: {caminho_arquivo}")
        return False

    # Corpo padrão, se não for informado
    corpo = corpo or """
    <p>Olá,</p>
    <p>Segue em anexo o relatório de faturamento gerado automaticamente pelo sistema.</p>
    <p>Atenciosamente,<br>
    <b>Equipe de Automação</b></p>
    """

    try:
        yag = yagmail.SMTP(SMTP_USER, SMTP_PASS)
        yag.send(
            to=destinatarios,
            subject=assunto,
            contents=corpo,
            attachments=caminho_arquivo,
        )
        logger.info(f"E-mail enviado com sucesso para: {', '.join(destinatarios)}")
        return True

    except Exception as e:
        logger.exception(f"Erro ao enviar e-mail: {e}")
        return False


# =========================
# EXECUÇÃO DIRETA (TESTE)
# =========================
if __name__ == "__main__":
    sucesso = enviar_relatorio(
        caminho_arquivo="dados/relatorio_faturamento.xlsx",
        destinatarios=["usuario@empresa.com"],
        assunto="Relatório de Faturamento - Outubro",
    )
    if sucesso:
        print("✅ E-mail enviado com sucesso!")
    else:
        print("❌ Falha no envio do e-mail. Verifique os logs.")
