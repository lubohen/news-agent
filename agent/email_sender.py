"""
email_sender.py
Envia a newsletter HTML por e-mail via Outlook SMTP (App Password).

Pré-requisito:
  - Ativar verificação em 2 etapas na conta Google
  - Gerar uma "Senha de app" em: https://myaccount.google.com/apppasswords
  - Preencher EMAIL_SENDER e EMAIL_APP_PASSWORD no arquivo .env
"""

import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date
from typing import List, Dict

from jinja2 import Environment, FileSystemLoader, select_autoescape
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("news-agent.email")

SMTP_HOST = os.getenv("EMAIL_SMTP_HOST", "smtp-mail.outlook.com")
SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "587"))
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD", "")
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT", "")


def _render_html(articles: List[Dict]) -> str:
    """Renderiza o template HTML da newsletter com os artigos."""
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("newsletter.html")

    month_names = [
        "", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
        "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
    ]
    today = date.today()
    formatted_date = f"{today.day} de {month_names[today.month]} de {today.year}"

    return template.render(
        articles=articles,
        today=formatted_date,
        total=len(articles),
    )


def _build_plain_text(articles: List[Dict]) -> str:
    """Gera versão texto simples como fallback do e-mail."""
    today = date.today().strftime("%d/%m/%Y")
    lines = [f"Newsletter Tech & AI — {today}", "=" * 40, ""]

    for i, article in enumerate(articles, 1):
        lines.append(f"{i}. {article['title']}")
        if article.get("source"):
            lines.append(f"   Fonte: {article['source']}")
        if article.get("summary"):
            lines.append(f"   {article['summary']}")
        if article.get("link"):
            lines.append(f"   Leia mais: {article['link']}")
        lines.append("")

    lines.append("─" * 40)
    lines.append("Newsletter gerada automaticamente pelo News Agent.")
    return "\n".join(lines)


def send_newsletter_email(articles: List[Dict]) -> None:
    """
    Envia a newsletter com os artigos para EMAIL_RECIPIENT via Outlook SMTP.

    Lança ValueError se as credenciais não estiverem configuradas.
    """
    missing = [
        var for var in ("EMAIL_SENDER", "EMAIL_APP_PASSWORD", "EMAIL_RECIPIENT")
        if not os.getenv(var)
    ]
    if missing:
        raise ValueError(
            f"Variáveis de e-mail não configuradas: {', '.join(missing)}. "
            "Preencha o arquivo .env com suas credenciais."
        )

    today_str = date.today().strftime("%d/%m/%Y")
    subject = f"\U0001f4f0 Newsletter Tech & AI — {today_str}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"News Agent <{EMAIL_SENDER}>"
    msg["To"] = EMAIL_RECIPIENT

    msg.attach(MIMEText(_build_plain_text(articles), "plain", "utf-8"))
    msg.attach(MIMEText(_render_html(articles), "html", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_APP_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, msg.as_string())
        logger.info(f"Newsletter enviada para {EMAIL_RECIPIENT}.")
    except smtplib.SMTPAuthenticationError:
        raise RuntimeError(
            "Falha de autentificação SMTP. Verifique EMAIL_SENDER e EMAIL_APP_PASSWORD. "
            "Para Outlook: ative a verificação em 2 etapas e gere uma Senha de App em "
            "https://account.microsoft.com/security"
        )
