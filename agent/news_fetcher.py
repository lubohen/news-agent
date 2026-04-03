"""
news_fetcher.py
Busca as 10 notícias mais relevantes de Tecnologia/Dados/AI
via feeds RSS públicos (Google News + portais especializados).
"""

import re
import logging
from typing import List, Dict

import feedparser
from bs4 import BeautifulSoup

logger = logging.getLogger("news-agent.fetcher")

# ─── Feeds RSS gratuitos e públicos ────────────────────────────────────────────
RSS_FEEDS = [
    # Google News em PT-BR — Inteligência Artificial
    "https://news.google.com/rss/search?q=intelig%C3%AAncia+artificial+machine+learning&hl=pt-BR&gl=BR&ceid=BR:pt-419",
    # Google News em PT-BR — Dados / Data Science
    "https://news.google.com/rss/search?q=data+science+engenharia+de+dados+big+data&hl=pt-BR&gl=BR&ceid=BR:pt-419",
    # Google News em PT-BR — LLM / GenAI
    "https://news.google.com/rss/search?q=LLM+GenAI+ChatGPT+Gemini+Claude+tecnologia&hl=pt-BR&gl=BR&ceid=BR:pt-419",
    # TechCrunch — AI (EN)
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    # VentureBeat — AI (EN)
    "https://venturebeat.com/category/ai/feed/",
    # MIT Technology Review (EN)
    "https://www.technologyreview.com/feed/",
    # InfoQ Brasil (PT-BR)
    "https://www.infoq.com/br/feed/",
]

# Palavras-chave para filtrar artigos relevantes
AI_DATA_KEYWORDS = [
    "inteligência artificial", "ia", " ai ", "machine learning", "deep learning",
    "data science", "big data", "llm", "gpt", "llama", "generative", "generativa",
    "dados", "data engineering", "engenharia de dados", "mlops", "neural",
    "chatgpt", "claude", "gemini", "openai", "anthropic", "hugging face",
    "transformer", "pytorch", "tensorflow", "databricks", "snowflake", "dbt",
    "apache spark", "kafka", "pipeline de dados", "model", "modelo",
    "algoritmo", "automação", "automate", "copilot", "agente",
]


def _clean_html(raw: str) -> str:
    """Remove tags HTML e normaliza espaços em branco."""
    if not raw:
        return ""
    soup = BeautifulSoup(raw, "lxml")
    text = soup.get_text(separator=" ")
    return re.sub(r"\s+", " ", text).strip()


def _is_relevant(entry: dict) -> bool:
    """Verifica se o artigo está relacionado a Dados/AI/Tecnologia."""
    title = (entry.get("title") or "").lower()
    summary = (entry.get("summary") or "").lower()
    combined = f"{title} {summary}"
    return any(kw in combined for kw in AI_DATA_KEYWORDS)


def _extract_source(entry: dict) -> str:
    """Extrai o nome da fonte do artigo."""
    if hasattr(entry, "source") and entry.source:
        return entry.source.get("title", "")
    if entry.get("author"):
        return entry.author
    return ""


def _parse_entry(entry: dict) -> Dict:
    """Converte uma entrada de feed em dicionário padronizado."""
    title = _clean_html(entry.get("title", "Sem título"))
    summary_raw = entry.get("summary") or entry.get("description") or ""
    summary = _clean_html(summary_raw)

    # Limita resumo a 350 caracteres
    if len(summary) > 350:
        summary = summary[:347] + "..."

    return {
        "title": title,
        "summary": summary if summary and summary.lower() != title.lower() else "",
        "source": _extract_source(entry),
        "link": entry.get("link", ""),
        "published": entry.get("published", ""),
    }


def fetch_top_news(limit: int = 10) -> List[Dict]:
    """
    Percorre os feeds RSS, filtra por palavras-chave relacionadas a Dados/AI
    e retorna as `limit` notícias mais recentes sem duplicatas.
    """
    seen_titles: set = set()
    articles: List[Dict] = []

    for feed_url in RSS_FEEDS:
        if len(articles) >= limit:
            break

        try:
            feed = feedparser.parse(feed_url, request_headers={"User-Agent": "Mozilla/5.0"})
            logger.debug(f"Feed '{feed_url}': {len(feed.entries)} entradas encontradas.")

            for entry in feed.entries:
                if len(articles) >= limit:
                    break

                if not _is_relevant(entry):
                    continue

                parsed = _parse_entry(entry)

                # Deduplica pelo título normalizado
                title_key = re.sub(r"\W+", "", parsed["title"].lower())
                if title_key in seen_titles:
                    continue

                seen_titles.add(title_key)
                articles.append(parsed)

        except Exception as exc:
            logger.warning(f"Falha ao processar feed '{feed_url}': {exc}")

    logger.info(f"{len(articles)} artigos coletados de {len(RSS_FEEDS)} feeds.")
    return articles[:limit]
