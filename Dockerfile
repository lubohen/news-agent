FROM python:3.11-slim

WORKDIR /app

# Instala dependências do sistema necessárias para lxml/beautifulsoup
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agent/ ./agent/

CMD ["python", "-u", "agent/main.py"]
