# News Agent — Tech & AI Newsletter

Agente que busca automaticamente as **10 principais notícias de Tecnologia, Dados e IA** e:

- 📱 Envia as **manchetes** para o seu **WhatsApp**
- 📧 Envia um **resumo completo** em formato de **newsletter HTML** por **e-mail**
- 🕗 Executa **diariamente** no horário que você configurar

Tudo **self-hosted**, **gratuito** e rodando via **Docker**.

---

## Stack

| Serviço | Tecnologia | Finalidade |
|---|---|---|
| Busca de notícias | Google News RSS + TechCrunch + VentureBeat | Coleta automática |
| WhatsApp | [Evolution API v2](https://github.com/EvolutionAPI/evolution-api) | Mensagem com manchetes — porta **8070** |
| E-mail | Outlook SMTP (App Password) | Newsletter HTML |
| Scheduler | APScheduler (Python) | Agendamento diário |
| Banco de dados | PostgreSQL 15 | Armazenamento da Evolution API |

---

## Pré-requisitos

- Docker e Docker Compose instalados
- Conta Outlook/Microsoft com **verificação em 2 etapas** ativada
- WhatsApp instalado no celular para escanear o QR Code

---

## Configuração (passo a passo)

### 1. Clone / navegue até o projeto

```bash
cd /data/projects/news-agent
```

### 2. Crie o arquivo `.env`

```bash
cp .env.example .env
```

Abra o `.env` e preencha **todos os campos** marcados com `<ALTERE_AQUI>`:

| Variável | O que preencher |
|---|---|
| `AUTHENTICATION_API_KEY` | Chave forte aleatória (ex: `openssl rand -hex 32`) |
| `POSTGRES_PASSWORD` | Senha do banco (qualquer string segura) |
| `WHATSAPP_RECIPIENT` | Seu número com DDI+DDD: `+5511999990000` |
| `EMAIL_SENDER` | `lubohen@outlook.com` |
| `EMAIL_APP_PASSWORD` | Senha de App da Microsoft (veja abaixo) |
| `EMAIL_RECIPIENT` | `lubohen@outlook.com` |

### 3. Gere uma Senha de App no Microsoft

1. Acesse [account.microsoft.com/security](https://account.microsoft.com/security)
2. Ative **Verificação em duas etapas**
3. Vá em **Senhas de aplicativo** → crie uma para "News Agent"
4. Cole os caracteres gerados em `EMAIL_APP_PASSWORD`

> ⚠️ Use a **Senha de App**, não sua senha normal do Outlook.

### 4. Suba os containers

```bash
docker compose up --build -d
```

### 5. Conecte o WhatsApp (primeira vez)

1. Acesse **http://localhost:8070/manager** no navegador
2. Faça login com `apikey: <valor de AUTHENTICATION_API_KEY>`
3. Clique na instância **`news-agent`**
4. Clique em **"Connect"** e escaneie o QR Code com seu celular
5. Aguarde o status mudar para **"open"** ✅

### 6. Verifique os logs

```bash
docker compose logs -f news-agent
```

O agente executa uma vez ao iniciar e depois diariamente às 8h (configurável).

---

## Personalização

### Horário de execução

No `.env`:
```env
SCHEDULE_HOUR=8
SCHEDULE_MINUTE=0
SCHEDULE_TIMEZONE=America/Sao_Paulo
```

### Feeds de notícias

Edite a lista `RSS_FEEDS` em `agent/news_fetcher.py` para adicionar ou remover fontes.

### Palavras-chave de filtro

Edite a lista `AI_DATA_KEYWORDS` em `agent/news_fetcher.py`.

---

## Comandos úteis

```bash
# Ver logs em tempo real
docker compose logs -f news-agent

# Forçar execução imediata
docker compose restart news-agent

# Parar tudo
docker compose down

# Parar e remover volumes (reset completo)
docker compose down -v
```

---

## Estrutura do projeto

```
news-agent/
├── docker-compose.yml          # Evolution API + PostgreSQL + Agent
├── Dockerfile                  # Imagem Python do agente
├── requirements.txt
├── .env.example                # Template de configuração
├── .env                        # Sua configuração (não versionar!)
├── .gitignore
├── logs/                       # Logs gerados em runtime
└── agent/
    ├── main.py                 # Orquestrador + APScheduler
    ├── news_fetcher.py         # Coleta notícias via RSS
    ├── whatsapp_sender.py      # Envia manchetes (Evolution API)
    ├── email_sender.py         # Envia newsletter (Outlook SMTP)
    └── templates/
        └── newsletter.html     # Template HTML do e-mail
```
