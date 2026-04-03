"""
main.py
Orquestrador do News Agent.

  1. Busca as 10 notícias de Tech/Dados/AI via feeds RSS.
  2. Envia as manchetes para o WhatsApp (Evolution API).
  3. Envia o resumo completo como newsletter por e-mail (Outlook SMTP).
  4. Repete diariamente no horário configurado em SCHEDULE_HOUR/SCHEDULE_MINUTE.

Variáveis de ambiente (arquivo .env):
  SCHEDULE_HOUR      — hora de execução (padrão: 8)
  SCHEDULE_MINUTE    — minuto de execução (padrão: 0)
  SCHEDULE_TIMEZONE  — fuso horário (padrão: America/Sao_Paulo)
  LOG_LEVEL          — nível de log (padrão: INFO)
"""

import os
import sys
import logging
from pathlib import Path

import pytz
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

# ─── Configuração de logging ───────────────────────────────────────────────────
load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_DIR = Path("/app/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)-8s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_DIR / "agent.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("news-agent")

# ─── Importações locais (após configurar logging) ──────────────────────────────
from news_fetcher import fetch_top_news          # noqa: E402
from whatsapp_sender import send_whatsapp_headlines  # noqa: E402
from email_sender import send_newsletter_email   # noqa: E402


# ─── Lógica principal ──────────────────────────────────────────────────────────

def run_agent() -> None:
    """
    Executa o pipeline completo:
    fetch  →  WhatsApp  →  E-mail
    """
    logger.info("=" * 55)
    logger.info("  Iniciando News Agent — buscando notícias...")
    logger.info("=" * 55)

    # 1. Busca notícias
    try:
        articles = fetch_top_news(limit=10)
    except Exception as exc:
        logger.error(f"Falha crítica ao buscar notícias: {exc}", exc_info=True)
        return

    if not articles:
        logger.warning("Nenhum artigo encontrado. Execução encerrada.")
        return

    logger.info(f"✔  {len(articles)} artigos coletados.")

    # 2. Envia manchetes para o WhatsApp
    try:
        send_whatsapp_headlines(articles)
        logger.info("✔  Manchetes enviadas ao WhatsApp.")
    except ConnectionError as exc:
        # WhatsApp não conectado — instrução clara para o usuário
        logger.error(f"WhatsApp desconectado: {exc}")
    except Exception as exc:
        logger.error(f"Falha ao enviar WhatsApp: {exc}", exc_info=True)

    # 3. Envia newsletter por e-mail
    try:
        send_newsletter_email(articles)
        logger.info("✔  Newsletter enviada por e-mail.")
    except Exception as exc:
        logger.error(f"Falha ao enviar e-mail: {exc}", exc_info=True)

    logger.info("Pipeline concluído.\n")


# ─── Scheduler ────────────────────────────────────────────────────────────────

def main() -> None:
    tz_name = os.getenv("SCHEDULE_TIMEZONE", "America/Sao_Paulo")
    hour = int(os.getenv("SCHEDULE_HOUR", "8"))
    minute = int(os.getenv("SCHEDULE_MINUTE", "0"))

    try:
        tz = pytz.timezone(tz_name)
    except pytz.UnknownTimeZoneError:
        logger.error(f"Fuso horário inválido: '{tz_name}'. Usando America/Sao_Paulo.")
        tz = pytz.timezone("America/Sao_Paulo")

    logger.info(
        f"Agente configurado — execução diária às {hour:02d}:{minute:02d} ({tz_name})"
    )

    # Executa imediatamente ao iniciar o container
    logger.info("Executando na inicialização do container...")
    run_agent()

    # Agenda execução diária
    scheduler = BlockingScheduler(timezone=tz)
    scheduler.add_job(
        run_agent,
        CronTrigger(hour=hour, minute=minute, timezone=tz),
        id="daily_news_agent",
        name="Daily Tech/AI News Agent",
        misfire_grace_time=300,  # tolera até 5 min de atraso
    )

    logger.info("Scheduler ativo. Aguardando próxima execução... (Ctrl+C para sair)")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("News Agent encerrado.")


if __name__ == "__main__":
    main()
