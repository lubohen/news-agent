"""
whatsapp_sender.py
Envia manchetes para o WhatsApp via CallMeBot (gratuito, sem infraestrutura).

Ativação — 1 vez pelo celular:
  1. Salve o número +34 644 59 10 10 na agenda (nome: CallMeBot)
  2. Envie a mensagem: I allow callmebot to send me messages
  3. Aguarde o bot responder com sua APIKEY
  4. Cole a APIKEY em CALLMEBOT_API_KEY no arquivo .env
"""

import os
import logging
from datetime import date
from typing import List, Dict
from urllib.parse import quote

import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("news-agent.whatsapp")

CALLMEBOT_URL      = "https://api.callmebot.com/whatsapp.php"
WHATSAPP_RECIPIENT = os.getenv("WHATSAPP_RECIPIENT", "")   # ex: +5511917121239
CALLMEBOT_API_KEY  = os.getenv("CALLMEBOT_API_KEY", "")

_TIMEOUT = 20


def _build_message(articles: List[Dict]) -> str:
    """Monta a mensagem formatada com as manchetes para o WhatsApp."""
    today = date.today().strftime("%d/%m/%Y")
    lines = [
        f"📰 *Tech & AI News — {today}*",
        "━━━━━━━━━━━━━━━━━━",
        "",
    ]
    for i, article in enumerate(articles, 1):
        source = f"  _{article['source']}_" if article.get("source") else ""
        lines.append(f"*{i}.* {article['title']}{source}")
        lines.append("")

    lines += [
        "━━━━━━━━━━━━━━━━━━",
        "📧 Resumo completo enviado por e-mail.",
    ]
    return "\n".join(lines)


def send_whatsapp_headlines(articles: List[Dict]) -> None:
    """
    Envia as manchetes para o WhatsApp via CallMeBot.

    Lança ValueError se WHATSAPP_RECIPIENT ou CALLMEBOT_API_KEY não estiverem
    configurados no .env.
    """
    if not WHATSAPP_RECIPIENT:
        raise ValueError(
            "WHATSAPP_RECIPIENT não configurado no .env. Ex: +5511917121239"
        )
    if not CALLMEBOT_API_KEY:
        raise ValueError(
            "CALLMEBOT_API_KEY não configurado no .env.\n"
            "Ative o CallMeBot enviando 'I allow callmebot to send me messages' "
            "para +34 684 728 023 no WhatsApp e cole a APIKEY recebida no .env."
        )

    # Remove o + do número (CallMeBot espera apenas dígitos)
    phone   = WHATSAPP_RECIPIENT.lstrip("+")
    message = _build_message(articles)
    encoded = quote(message)

    resp = requests.get(
        f"{CALLMEBOT_URL}?phone={phone}&text={encoded}&apikey={CALLMEBOT_API_KEY}",
        timeout=_TIMEOUT,
    )

    if resp.status_code == 200:
        logger.debug(f"CallMeBot resposta: {resp.text[:120]}")
    else:
        raise RuntimeError(
            f"CallMeBot retornou status {resp.status_code}: {resp.text[:200]}"
        )
