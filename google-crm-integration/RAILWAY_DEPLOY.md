# Guia Rápido de Deploy na Railway

Este guia fornece instruções passo a passo para fazer deploy da aplicação Google CRM Integration na Railway.

## 🚀 Passo a Passo

### 1. Preparar o Repositório

Certifique-se de que seu código está no GitHub e que o repositório está acessível.

### 2. Criar Projeto na Railway

1. Acesse https://railway.app
2. Faça login com sua conta GitHub
3. Clique em "New Project"
4. Selecione "Deploy from GitHub repo"
5. Conecte seu repositório GitHub
6. Selecione o repositório `google-crm-integration`

### 3. Configurar Variáveis de Ambiente

No dashboard do projeto Railway, vá em "Variables" e adicione todas as variáveis necessárias:

**Obrigatórias:**
- `SECRET_KEY` - Gere uma chave forte (ex: `openssl rand -hex 32`)
- `GOOGLE_CLIENT_ID` - Do Google Cloud Console
- `GOOGLE_CLIENT_SECRET` - Do Google Cloud Console
- `GOOGLE_REDIRECT_URI` - Será atualizado após obter o domínio
- `GOOGLE_ADS_DEVELOPER_TOKEN` - Do Google Ads API Center
- `GOOGLE_ADS_CLIENT_ID` - Do Google Cloud Console
- `GOOGLE_ADS_CLIENT_SECRET` - Do Google Cloud Console
- `GOOGLE_ADS_LOGIN_CUSTOMER_ID` - Seu Customer ID do Google Ads
- `GOOGLE_ANALYTICS_PROPERTY_ID` - Property ID do GA4
- `COUCHBASE_CONNECTION_STRING` - Connection string do Couchbase Cloud
- `COUCHBASE_USERNAME` - Usuário do Couchbase
- `COUCHBASE_PASSWORD` - Senha do Couchbase
- `KAFKA_BOOTSTRAP_SERVERS` - Bootstrap servers do Confluent Cloud
- `KAFKA_SASL_USERNAME` - API Key do Confluent Cloud
- `KAFKA_SASL_PASSWORD` - API Secret do Confluent Cloud

**Opcionais (com valores padrão):**
- `APP_ENV=production`
- `DEBUG=False`
- `APP_NAME=Google CRM Integration`
- `COUCHBASE_BUCKET_NAME=crm-data`
- `COUCHBASE_SCOPE_NAME=crm`
- `REDIS_URL` - Se usar Redis da Railway (veja passo 4)
- `CELERY_BROKER_URL` - URL do Redis para Celery
- `CELERY_RESULT_BACKEND` - URL do Redis para resultados

**Nota:** A Railway fornece automaticamente a variável `PORT` - não é necessário configurá-la.

### 4. Configurar Redis (Opcional)

Se você precisar de Redis para Celery:

1. No dashboard Railway, clique em "New" > "Database" > "Redis"
2. Railway criará automaticamente a variável `REDIS_URL`
3. Use essa URL nas variáveis `CELERY_BROKER_URL` e `CELERY_RESULT_BACKEND`:
   - `CELERY_BROKER_URL=<REDIS_URL>/1`
   - `CELERY_RESULT_BACKEND=<REDIS_URL>/2`

### 5. Configurar Domínio

1. No dashboard Railway, vá em "Settings" > "Networking"
2. Clique em "Generate Domain" para obter um domínio público
3. Anote o domínio gerado (ex: `seu-app.railway.app`)
4. **Importante:** Atualize a variável `GOOGLE_REDIRECT_URI` com:
   - `https://seu-app.railway.app/auth/google/callback`

### 6. Configurar Google OAuth Redirect URI

1. Acesse [Google Cloud Console](https://console.cloud.google.com)
2. Vá em "APIs & Services" > "Credentials"
3. Edite seu OAuth Client ID
4. Adicione a URL de callback da Railway:
   - `https://seu-app.railway.app/auth/google/callback`
5. Salve as alterações

### 7. Deploy

1. Railway detectará automaticamente o `Dockerfile` e fará o build
2. O deploy será feito automaticamente após o primeiro push
3. Acompanhe o processo em "Deployments"
4. Verifique os logs em "Deployments" > "View Logs"

### 8. Verificar Deploy

1. Após o deploy, acesse `https://seu-app.railway.app/health`
2. Você deve receber uma resposta JSON com o status "healthy"
3. Verifique se todos os serviços estão conectados:
   - `couchbase_connected: true`
   - `kafka_connected: true`

### 9. Testar a API

```bash
# Health check
curl https://seu-app.railway.app/health

# Documentação da API
# Acesse: https://seu-app.railway.app/docs
```

## 🔧 Configurar Workers Celery (Opcional)

Para executar workers Celery e o beat scheduler:

### Opção 1: Serviços Separados (Recomendado)

1. No projeto Railway, clique em "New Service"
2. Selecione "GitHub Repo" novamente
3. Selecione o mesmo repositório
4. Configure o comando de start:
   - Para Worker: `celery -A app.workers.celery_app worker --loglevel=info`
   - Para Beat: `celery -A app.workers.celery_app beat --loglevel=info`
5. Configure as mesmas variáveis de ambiente

### Opção 2: Usar Railway CLI

```bash
# Instalar Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link ao projeto
railway link

# Deploy worker
railway run celery -A app.workers.celery_app worker --loglevel=info
```

## 🐛 Troubleshooting

### Erro: "Port already in use"
- **Solução:** Railway fornece `PORT` automaticamente - não defina manualmente

### Erro: "Connection timeout" com Couchbase/Kafka
- **Solução:** Verifique se as URLs de conexão estão corretas e se os serviços estão acessíveis publicamente

### Erro: "Build failed"
- **Solução:** Verifique os logs de build em "Deployments" > "View Logs"
- Certifique-se de que o `Dockerfile` está na raiz do repositório

### Erro: "Health check failed"
- **Solução:** Verifique se o endpoint `/health` está funcionando
- Verifique os logs da aplicação

### Erro: "Environment variable not found"
- **Solução:** Verifique se todas as variáveis de ambiente obrigatórias estão configuradas
- Certifique-se de que não há erros de digitação nos nomes das variáveis

## 📊 Monitoramento

- **Logs:** Acesse "Deployments" > "View Logs" no dashboard Railway
- **Métricas:** Railway fornece métricas básicas de CPU, memória e rede
- **Health Checks:** Railway monitora automaticamente o endpoint `/health`

## 🔄 Deploy Automático

Railway faz deploy automático a cada push no repositório GitHub conectado. Para desabilitar:

1. Vá em "Settings" > "Source"
2. Desabilite "Auto Deploy"

## 📝 Notas Importantes

- A Railway fornece automaticamente a variável `PORT` - não é necessário configurá-la
- O endpoint `/health` é usado automaticamente para health checks
- Certifique-se de que todas as URLs de callback OAuth estão configuradas corretamente
- Para produção, configure `DEBUG=False` e `APP_ENV=production`
- Use HTTPS sempre (Railway fornece HTTPS automaticamente)

## 🆘 Suporte

Para mais informações, consulte:
- [Documentação da Railway](https://docs.railway.app)
- [Documentação do FastAPI](https://fastapi.tiangolo.com)
- README.md do projeto

