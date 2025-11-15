# Google CRM Integration

Integração completa do CRM com Google Ads e Google Analytics, utilizando Couchbase Cloud para armazenamento de dados e Confluent Cloud (Kafka) para streaming de eventos.

## 🚀 Recursos

- **Autenticação OAuth 2.0** com Google
- **Integração com Google Ads API** para captura de insights de campanhas e leads
- **Integração com Google Analytics (GA4)** para métricas de website
- **Armazenamento em Couchbase Cloud** (NoSQL escalável)
- **Event Streaming com Confluent Cloud (Kafka)** para processamento em tempo real
- **API REST com FastAPI** para acesso aos dados
- **Background Workers com Celery** para sincronização automática
- **Dockerizado** para fácil deployment

## 📋 Pré-requisitos

### Contas e Credenciais Necessárias

1. **Google Cloud Platform**
   - Projeto no GCP com APIs habilitadas:
     - Google Ads API
     - Google Analytics Data API
     - Google OAuth 2.0
   - Client ID e Client Secret OAuth
   - Developer Token do Google Ads
   - Property ID do Google Analytics (GA4)

2. **Couchbase Cloud**
   - Cluster criado em https://cloud.couchbase.com
   - Bucket criado (ex: `crm-data`)
   - Usuário com permissões apropriadas
   - Connection string do cluster

3. **Confluent Cloud**
   - Cluster Kafka criado em https://confluent.cloud
   - API Key e API Secret
   - Bootstrap servers URL
   - Tópicos criados:
     - `crm.leads`
     - `crm.insights`
     - `crm.events`

4. **Sistema Local**
   - Python 3.11+
   - Docker e Docker Compose (opcional)
   - Redis (se não usar Docker)

## 🛠️ Instalação

### Opção 1: Com Docker (Recomendado)

```bash
# 1. Clone o repositório
cd /home/user/Ninetwo-CRM/google-crm-integration

# 2. Configure as variáveis de ambiente
cp .env.example .env
# Edite o arquivo .env com suas credenciais

# 3. Build e execute os containers
docker-compose up -d

# 4. Verifique os logs
docker-compose logs -f api
```

### Opção 2: Instalação Local

```bash
# 1. Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Configure as variáveis de ambiente
cp .env.example .env
# Edite o arquivo .env com suas credenciais

# 4. Inicie o Redis (necessário)
redis-server

# 5. Execute a API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

# 6. Em outro terminal, execute o worker Celery
celery -A app.workers.celery_app worker --loglevel=info

# 7. Em outro terminal, execute o beat scheduler
celery -A app.workers.celery_app beat --loglevel=info
```

## ⚙️ Configuração

### 1. Configurar Google Cloud

#### Habilitar APIs
1. Acesse [Google Cloud Console](https://console.cloud.google.com)
2. Selecione seu projeto
3. Vá em "APIs & Services" > "Library"
4. Habilite:
   - Google Ads API
   - Google Analytics Data API

#### Criar Credenciais OAuth
1. Vá em "APIs & Services" > "Credentials"
2. Clique em "Create Credentials" > "OAuth client ID"
3. Tipo: Web application
4. Nome: "Google CRM Integration"
5. Authorized redirect URIs:
   - `http://localhost:8080/auth/google/callback` (desenvolvimento)
   - Seu domínio de produção
6. Copie Client ID e Client Secret para o `.env`

#### Google Ads Developer Token
1. Acesse [Google Ads API Center](https://ads.google.com/aw/apicenter)
2. Solicite um Developer Token
3. Copie para `GOOGLE_ADS_DEVELOPER_TOKEN` no `.env`

### 2. Configurar Couchbase Cloud

```bash
# No terminal do cluster Couchbase, execute:

# Criar bucket
cbq> CREATE BUCKET `crm-data` WITH maxBucketCount = 3;

# Criar scope
cbq> CREATE SCOPE `crm-data`.`crm`;

# Criar collections
cbq> CREATE COLLECTION `crm-data`.`crm`.`leads`;
cbq> CREATE COLLECTION `crm-data`.`crm`.`insights`;
cbq> CREATE COLLECTION `crm-data`.`crm`.`users`;

# Criar índices
cbq> CREATE PRIMARY INDEX ON `crm-data`.`crm`.`leads`;
cbq> CREATE PRIMARY INDEX ON `crm-data`.`crm`.`insights`;
cbq> CREATE PRIMARY INDEX ON `crm-data`.`crm`.`users`;
```

### 3. Configurar Confluent Cloud

1. Acesse [Confluent Cloud](https://confluent.cloud)
2. Crie um cluster Kafka
3. Crie os tópicos:
   - `crm.leads` (3 partitions, 7 days retention)
   - `crm.insights` (3 partitions, 7 days retention)
   - `crm.events` (3 partitions, 7 days retention)
4. Crie API Key em "Data Integration" > "API Keys"
5. Copie Bootstrap servers, API Key e Secret para o `.env`

## 📖 Uso da API

### 1. Autenticar com Google

```bash
# Obter URL de autorização
curl -X GET "http://localhost:8080/auth/google/authorize?user_id=user123"

# Resposta:
{
  "authorization_url": "https://accounts.google.com/o/oauth2/auth?...",
  "state": "user123:1234567890"
}

# Redirecione o usuário para authorization_url
# Após autorizar, Google redirecionará para /auth/google/callback
```

### 2. Criar um Lead Manualmente

```bash
curl -X POST "http://localhost:8080/leads/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "João Silva",
    "email": "joao@example.com",
    "phone": "+5511999999999",
    "company": "Empresa XYZ",
    "user_id": "user123",
    "notes": "Interessado em nossos serviços"
  }'
```

### 3. Sincronizar Dados do Google

```bash
# Sincronizar últimos 30 dias
curl -X POST "http://localhost:8080/insights/sync/user123?days_back=30"

# Resposta:
{
  "success": true,
  "message": "Data sync completed",
  "results": {
    "user_id": "user123",
    "ads_insights": 150,
    "analytics_insights": 120,
    "leads": 5,
    "errors": []
  }
}
```

### 4. Obter Insights do Google Ads

```bash
curl -X GET "http://localhost:8080/insights/google-ads/user123?limit=10"
```

### 5. Obter Insights do Google Analytics

```bash
curl -X GET "http://localhost:8080/insights/google-analytics/user123?limit=10"
```

### 6. Obter Resumo Agregado

```bash
curl -X GET "http://localhost:8080/insights/summary/user123?days=30"

# Resposta:
{
  "success": true,
  "summary": {
    "user_id": "user123",
    "period_days": 30,
    "google_ads": {
      "impressions": 50000,
      "clicks": 1250,
      "cost": 500.00,
      "conversions": 25,
      "ctr": 2.5,
      "cpc": 0.40
    },
    "google_analytics": {
      "sessions": 3000,
      "users": 2500,
      "revenue": 2500.00
    },
    "performance": {
      "roi_percentage": 400.0,
      "roas": 5.0
    }
  }
}
```

### 7. Listar Leads

```bash
curl -X GET "http://localhost:8080/leads/?user_id=user123&limit=50"
```

### 8. Health Check

```bash
curl -X GET "http://localhost:8080/health"

# Resposta:
{
  "status": "healthy",
  "service": "Google CRM Integration",
  "environment": "development",
  "couchbase_connected": true,
  "kafka_connected": true
}
```

## 📊 Documentação da API

Após iniciar o servidor, acesse:

- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc

## 🔄 Sincronização Automática

O sistema executa sincronização automática a cada intervalo configurado (padrão: 15 minutos).

Para alterar o intervalo:

```env
# No arquivo .env
SYNC_INTERVAL_MINUTES=30  # Sincronizar a cada 30 minutos
```

## 📁 Estrutura do Projeto

```
google-crm-integration/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Aplicação FastAPI principal
│   ├── config.py               # Configurações
│   ├── api/                    # Rotas da API
│   │   ├── auth_routes.py      # Autenticação OAuth
│   │   ├── lead_routes.py      # CRUD de leads
│   │   └── insight_routes.py   # Endpoints de insights
│   ├── auth/                   # Autenticação
│   │   └── google_oauth.py     # Handler OAuth Google
│   ├── integrations/           # Integrações externas
│   │   ├── google_ads.py       # Cliente Google Ads
│   │   └── google_analytics.py # Cliente Google Analytics
│   ├── models/                 # Modelos de dados
│   │   ├── lead.py
│   │   ├── insight.py
│   │   └── user.py
│   ├── services/               # Serviços de negócio
│   │   ├── couchbase_service.py
│   │   ├── kafka_service.py
│   │   └── sync_service.py
│   └── workers/                # Background workers
│       ├── celery_app.py
│       └── tasks.py
├── config/                     # Configurações
├── tests/                      # Testes
├── requirements.txt            # Dependências Python
├── Dockerfile                  # Imagem Docker
├── docker-compose.yml          # Orquestração Docker
├── .env.example                # Template de variáveis
├── .gitignore
└── README.md                   # Este arquivo
```

## 🧪 Testes

```bash
# Instalar dependências de teste
pip install pytest pytest-asyncio pytest-cov httpx

# Executar testes
pytest

# Com cobertura
pytest --cov=app --cov-report=html
```

## 🔒 Segurança

- **OAuth 2.0** para autenticação Google
- **Tokens criptografados** armazenados no Couchbase
- **HTTPS obrigatório** em produção
- **Rate limiting** recomendado
- **Validação de dados** com Pydantic
- **CORS** configurável

## 🚀 Deploy em Produção

### Deploy na Railway (Recomendado)

A Railway é uma plataforma de deploy simplificada que suporta Docker e oferece deploy automático a partir do GitHub.

#### Pré-requisitos

1. Conta na [Railway](https://railway.app)
2. Repositório GitHub com o código do projeto
3. Todas as credenciais necessárias (Google Cloud, Couchbase, Confluent, etc.)

#### Passo a Passo

1. **Criar Projeto na Railway**
   - Acesse https://railway.app
   - Clique em "New Project"
   - Selecione "Deploy from GitHub repo"
   - Conecte seu repositório GitHub
   - Selecione o repositório `google-crm-integration`

2. **Configurar Variáveis de Ambiente**
   - No dashboard do projeto Railway, vá em "Variables"
   - Adicione todas as variáveis de ambiente necessárias:

   ```env
   # Application Settings
   APP_ENV=production
   APP_NAME=Google CRM Integration
   APP_HOST=0.0.0.0
   DEBUG=False
   SECRET_KEY=<gere-uma-chave-forte-aqui>
   
   # Google OAuth Configuration
   GOOGLE_CLIENT_ID=<seu-google-client-id>
   GOOGLE_CLIENT_SECRET=<seu-google-client-secret>
   GOOGLE_REDIRECT_URI=https://seu-app.railway.app/auth/google/callback
   
   # Google Ads API
   GOOGLE_ADS_DEVELOPER_TOKEN=<seu-developer-token>
   GOOGLE_ADS_CLIENT_ID=<seu-ads-client-id>
   GOOGLE_ADS_CLIENT_SECRET=<seu-ads-client-secret>
   GOOGLE_ADS_LOGIN_CUSTOMER_ID=<seu-customer-id>
   
   # Google Analytics API
   GOOGLE_ANALYTICS_PROPERTY_ID=<seu-property-id>
   
   # Couchbase Cloud Configuration
   COUCHBASE_CONNECTION_STRING=<sua-connection-string>
   COUCHBASE_USERNAME=<seu-username>
   COUCHBASE_PASSWORD=<sua-senha>
   COUCHBASE_BUCKET_NAME=crm-data
   COUCHBASE_SCOPE_NAME=crm
   
   # Confluent Kafka Configuration
   KAFKA_BOOTSTRAP_SERVERS=<seus-bootstrap-servers>
   KAFKA_SASL_USERNAME=<sua-api-key>
   KAFKA_SASL_PASSWORD=<sua-api-secret>
   KAFKA_SECURITY_PROTOCOL=SASL_SSL
   KAFKA_SASL_MECHANISM=PLAIN
   
   # Redis Configuration (Railway pode provisionar Redis)
   REDIS_URL=<redis-url-da-railway-ou-externa>
   CELERY_BROKER_URL=<redis-url>/1
   CELERY_RESULT_BACKEND=<redis-url>/2
   
   # Sync Settings
   SYNC_INTERVAL_MINUTES=15
   SYNC_DAYS_LOOKBACK=30
   ```

   **Nota:** A Railway fornece automaticamente a variável `PORT` - não é necessário configurá-la manualmente.

3. **Configurar Redis (Opcional)**
   - Railway oferece Redis como addon
   - No dashboard, clique em "New" > "Database" > "Redis"
   - Railway configurará automaticamente a variável `REDIS_URL`
   - Use essa URL nas variáveis `CELERY_BROKER_URL` e `CELERY_RESULT_BACKEND`

4. **Configurar Domínio**
   - No dashboard, vá em "Settings" > "Networking"
   - Clique em "Generate Domain" para obter um domínio público
   - Ou configure um domínio customizado em "Custom Domain"
   - **Importante:** Atualize `GOOGLE_REDIRECT_URI` com o domínio gerado

5. **Configurar Google OAuth Redirect URI**
   - No [Google Cloud Console](https://console.cloud.google.com)
   - Vá em "APIs & Services" > "Credentials"
   - Edite seu OAuth Client ID
   - Adicione a URL de callback da Railway:
     - `https://seu-app.railway.app/auth/google/callback`
   - Salve as alterações

6. **Deploy**
   - Railway detectará automaticamente o `Dockerfile` e fará o build
   - O deploy será feito automaticamente a cada push no repositório
   - Acompanhe o processo em "Deployments"

7. **Verificar Deploy**
   - Após o deploy, acesse `https://seu-app.railway.app/health`
   - Verifique os logs em "Deployments" > "View Logs"

#### Configuração de Health Check

A Railway utiliza automaticamente o endpoint `/health` para health checks. Certifique-se de que o endpoint está funcionando corretamente.

#### Worker e Beat (Celery)

Para executar workers Celery e o beat scheduler na Railway:

1. **Opção 1: Serviços Separados (Recomendado)**
   - Crie 3 serviços separados no mesmo projeto Railway:
     - **API:** Deploy do Dockerfile padrão (API FastAPI)
     - **Worker:** Deploy do mesmo Dockerfile com comando: `celery -A app.workers.celery_app worker --loglevel=info`
     - **Beat:** Deploy do mesmo Dockerfile com comando: `celery -A app.workers.celery_app beat --loglevel=info`

2. **Opção 2: Usar Procfile**
   - Crie um arquivo `Procfile` na raiz do projeto:
   ```
   web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   worker: celery -A app.workers.celery_app worker --loglevel=info
   beat: celery -A app.workers.celery_app beat --loglevel=info
   ```
   - Configure Railway para usar o Procfile (requer buildpack)

#### Monitoramento

- **Logs:** Acesse "Deployments" > "View Logs" no dashboard Railway
- **Métricas:** Railway fornece métricas básicas de CPU, memória e rede
- **Health Checks:** Railway monitora automaticamente o endpoint `/health`

#### Troubleshooting

- **Erro de conexão com Couchbase/Kafka:** Verifique se as URLs de conexão estão corretas e se os serviços estão acessíveis publicamente
- **Erro de porta:** Railway fornece `PORT` automaticamente - não defina manualmente
- **Build falhando:** Verifique os logs de build em "Deployments"
- **Timeout na inicialização:** Verifique se os serviços externos (Couchbase, Kafka) estão acessíveis

### Docker Compose para Produção (Alternativa)

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto é proprietário e confidencial.

## 📧 Suporte

Para suporte, entre em contato através de: seu-email@exemplo.com

## 🙏 Agradecimentos

- Google Ads API
- Google Analytics Data API
- Couchbase
- Confluent
- FastAPI
- Celery

---

**Desenvolvido com ❤️ para Ninetwo CRM**
