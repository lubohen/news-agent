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


def _build_message(articles: List[Dict], part: int = 1, total_parts: int = 1) -> str:
    """Monta a mensagem formatada com as manchetes para o WhatsApp."""
    today = date.today().strftime("%d/%m/%Y")
    part_label = f" ({part}/{total_parts})" if total_parts > 1 else ""
    lines = [
        f"📰 *Tech & AI News — {today}*{part_label}",
        "━━━━━━━━━━━━━━━━━━",
        "",
    ]
    for i, article in enumerate(articles, 1):
        # Limita título a 120 chars para não estourar a URL
        title = article['title'][:120] + ("…" if len(article['title']) > 120 else "")
        source = f"  _{article['source']}_" if article.get("source") else ""
        lines.append(f"*{i}.* {title}{source}")
        lines.append("")

    lines += [
        "━━━━━━━━━━━━━━━━━━",
    ]
    if part == total_parts:
        lines.append("📧 Resumo completo enviado por e-mail.")
    return "\n".join(lines)


def _send_request(phone: str, message: str) -> None:
    """Envia uma requisição para a API do CallMeBot."""
    encoded = quote(message)
    resp = requests.get(
        f"{CALLMEBOT_URL}?phone={phone}&text={encoded}&apikey={CALLMEBOT_API_KEY}",
        timeout=_TIMEOUT,
    )
    if resp.status_code != 200:
        raise RuntimeError(
            f"CallMeBot retornou status {resp.status_code}: {resp.text[:200]}"
        )
    logger.debug(f"CallMeBot resposta: {resp.text[:120]}")


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

    # Divide em lotes de 5 para não estourar o limite de URL do CallMeBot
    batch_size = 5
    batches = [articles[i:i + batch_size] for i in range(0, len(articles), batch_size)]
    total_parts = len(batches)

    for idx, batch in enumerate(batches, 1):
        # Renumera os artigos de acordo com a posição global
        numbered = []
        for j, article in enumerate(batch):
            numbered.append({**article, "_global_n": (idx - 1) * batch_size + j + 1})

        # Reconstrói com numeração global
        today = date.today().strftime("%d/%m/%Y")
        part_label = f" ({idx}/{total_parts})" if total_parts > 1 else ""
        lines = [f"📰 *Tech & AI News — {today}*{part_label}", "━━━━━━━━━━━━━━━━━━", ""]
        for art in numbered:
            title = art['title'][:120] + ("…" if len(art['title']) > 120 else "")
            source = f"  _{art['source']}_" if art.get("source") else ""
            lines.append(f"*{art['_global_n']}.* {title}{source}")
            lines.append("")
        lines.append("━━━━━━━━━━━━━━━━━━")
        if idx == total_parts:
            lines.append("📧 Resumo completo enviado por e-mail.")

        _send_request(phone, "\n".join(lines))
        logger.debug(f"Lote {idx}/{total_parts} enviado.")
