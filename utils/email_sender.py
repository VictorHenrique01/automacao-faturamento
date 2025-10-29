import yagmail
import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

SMTP_USER = os.getenv("EMAIL_USER")
SMTP_PASS = os.getenv("EMAIL_PASS")

def enviar_relatorio(caminho_arquivo: str, destinatarios: List[str], assunto: str = "Relatório de Faturamento"):
    if not SMTP_USER or not SMTP_PASS:
        raise EnvironmentError("Configure EMAIL_USER e EMAIL_PASS no .env para usar envio de email.")
    yag = yagmail.SMTP(SMTP_USER, SMTP_PASS)
    body = "Segue em anexo o relatório de faturamento gerado automaticamente."
    yag.send(to=destinatarios, subject=assunto, contents=body, attachments=caminho_arquivo)
