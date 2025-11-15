# Deploy do Frappe Bench (CRM + Insights) na Railway

Este guia explica como fazer deploy do **Frappe Bench** com os apps **CRM** e **Insights** na Railway.

## 📋 Estrutura do Projeto

- **Frappe Bench**: Framework base que gerencia os apps
- **CRM App**: Aplicativo de CRM (Customer Relationship Management)
- **Insights App**: Aplicativo de análise de dados
- **google-crm-integration**: Integração separada (FastAPI) - ver `../google-crm-integration/`

## 🚀 Deploy na Railway

### Pré-requisitos

1. Conta na [Railway](https://railway.app)
2. Repositório GitHub com o código
3. Banco de dados MariaDB/MySQL (Railway pode provisionar)
4. Redis (Railway pode provisionar)

### Passo a Passo

#### 1. Criar Projeto na Railway

1. Acesse https://railway.app
2. Clique em "New Project"
3. Selecione "Deploy from GitHub repo"
4. Conecte seu repositório
5. Selecione o repositório

#### 2. Provisionar Serviços Necessários

**MariaDB/MySQL:**
- No dashboard, clique em "New" > "Database" > "MySQL"
- Railway criará automaticamente variáveis:
  - `MYSQL_HOST`
  - `MYSQL_PORT`
  - `MYSQL_DATABASE`
  - `MYSQL_USER`
  - `MYSQL_PASSWORD`
  - `MYSQL_URL`

**Redis:**
- Clique em "New" > "Database" > "Redis"
- Railway criará automaticamente:
  - `REDIS_URL`

#### 3. Configurar Variáveis de Ambiente

No dashboard do projeto Railway, vá em "Variables" e adicione:

```env
# Application
APP_ENV=production
PORT=8000

# Frappe Bench Configuration
FRAPPE_SITE_NAME=crm.localhost
FRAPPE_ADMIN_PASSWORD=<senha-admin-segura>

# Database (usar variáveis do MySQL da Railway)
DB_HOST=${MYSQL_HOST}
DB_PORT=${MYSQL_PORT}
DB_NAME=${MYSQL_DATABASE}
DB_USER=${MYSQL_USER}
DB_PASSWORD=${MYSQL_PASSWORD}

# Redis (usar variável do Redis da Railway)
REDIS_CACHE_URL=${REDIS_URL}
REDIS_QUEUE_URL=${REDIS_URL}
REDIS_SOCKETIO_URL=${REDIS_URL}

# Bench Configuration
BENCH_PATH=/home/frappe/frappe-bench
APPS_PATH=/home/frappe/frappe-bench/apps
SITES_PATH=/home/frappe/frappe-bench/sites

# Security
SECRET_KEY=<gere-uma-chave-forte>
ENCRYPTION_KEY=<gere-uma-chave-forte>

# Email (opcional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=1
MAIL_USERNAME=<seu-email>
MAIL_PASSWORD=<sua-senha>
```

**Gerar chaves secretas:**
```bash
# SECRET_KEY
openssl rand -hex 32

# ENCRYPTION_KEY
openssl rand -hex 32
```

#### 4. Configurar o Deploy

1. Railway detectará automaticamente o `Dockerfile` no diretório `frappe-bench`
2. Configure o **Root Directory** no Railway:
   - Vá em "Settings" > "Source"
   - Defina "Root Directory" como `frappe-bench`

#### 5. Configurar Domínio

1. No dashboard, vá em "Settings" > "Networking"
2. Clique em "Generate Domain" para obter um domínio público
3. Anote o domínio (ex: `seu-frappe.railway.app`)

#### 6. Inicializar o Bench (Primeira Vez)

Para a primeira vez, você pode precisar inicializar o bench. Crie um script de inicialização:

**Opção 1: Via Railway CLI**

```bash
# Instalar Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link ao projeto
railway link

# Executar comandos de inicialização
railway run bench --site crm.localhost migrate
railway run bench --site crm.localhost build
```

**Opção 2: Via Script de Inicialização**

Crie um script `init.sh` que será executado no primeiro deploy:

```bash
#!/bin/bash
set -e

# Verificar se o site já existe
if [ ! -f "sites/crm.localhost/site_config.json" ]; then
    echo "Inicializando novo site..."
    
    # Criar site
    bench new-site crm.localhost \
        --db-host ${DB_HOST} \
        --db-port ${DB_PORT} \
        --db-name ${DB_NAME} \
        --db-user ${DB_USER} \
        --db-password ${DB_PASSWORD} \
        --admin-password ${FRAPPE_ADMIN_PASSWORD} \
        --no-mariadb-socket
    
    # Instalar apps
    bench --site crm.localhost install-app crm
    bench --site crm.localhost install-app insights
    
    # Configurações
    bench --site crm.localhost set-config developer_mode 0
    bench --site crm.localhost set-config mute_emails 0
    bench --site crm.localhost clear-cache
fi

# Build assets
bench build --app crm
bench build --app insights

# Migrate database
bench --site crm.localhost migrate

echo "Inicialização concluída!"
```

#### 7. Atualizar Dockerfile para Inicialização

Atualize o `Dockerfile` para executar a inicialização:

```dockerfile
# ... código anterior ...

# Copy initialization script
COPY init.sh ./init.sh
RUN chmod +x ./init.sh

# Run initialization on first start
CMD sh -c "./init.sh && bench serve --port ${PORT:-8000} --host 0.0.0.0"
```

#### 8. Workers e Scheduler (Serviços Adicionais)

Para executar workers e scheduler, crie serviços separados:

**Worker Service:**
- Comando: `bench worker`
- Mesmas variáveis de ambiente

**Scheduler Service:**
- Comando: `bench schedule`
- Mesmas variáveis de ambiente

**SocketIO Service (opcional):**
- Comando: `node apps/frappe/socketio.js`
- Mesmas variáveis de ambiente

### Configuração do common_site_config.json

Atualize `sites/common_site_config.json` para usar variáveis de ambiente:

```json
{
  "db_host": "${DB_HOST}",
  "db_port": ${DB_PORT},
  "db_name": "${DB_NAME}",
  "db_user": "${DB_USER}",
  "db_password": "${DB_PASSWORD}",
  "redis_cache": "${REDIS_CACHE_URL}",
  "redis_queue": "${REDIS_QUEUE_URL}",
  "redis_socketio": "${REDIS_SOCKETIO_URL}",
  "webserver_port": 8000,
  "socketio_port": 9000,
  "serve_default_site": true
}
```

## 🔧 Comandos Úteis

### Via Railway CLI

```bash
# Migrar banco de dados
railway run bench --site crm.localhost migrate

# Build assets
railway run bench build --app crm
railway run bench build --app insights

# Limpar cache
railway run bench --site crm.localhost clear-cache

# Console Python
railway run bench --site crm.localhost console

# Backup
railway run bench --site crm.localhost backup
```

## 🐛 Troubleshooting

### Erro: "Site not found"
- **Solução**: Execute `bench new-site crm.localhost` via Railway CLI

### Erro: "Database connection failed"
- **Solução**: Verifique se as variáveis de ambiente do MySQL estão corretas
- Certifique-se de que o MySQL está acessível publicamente

### Erro: "Redis connection failed"
- **Solução**: Verifique se `REDIS_URL` está configurado corretamente

### Erro: "Port already in use"
- **Solução**: Railway fornece `PORT` automaticamente - use `${PORT}` no comando

### Assets não carregam
- **Solução**: Execute `bench build --app crm` e `bench build --app insights`

## 📊 Monitoramento

- **Logs**: Acesse "Deployments" > "View Logs" no dashboard Railway
- **Métricas**: Railway fornece métricas de CPU, memória e rede
- **Health Check**: Railway monitora automaticamente o endpoint `/api/method/ping`

## 🔄 Deploy Automático

Railway faz deploy automático a cada push no repositório. Para desabilitar:

1. Vá em "Settings" > "Source"
2. Desabilite "Auto Deploy"

## 📝 Notas Importantes

- O Frappe Bench requer **MariaDB/MySQL** e **Redis**
- Use serviços provisionados pela Railway para melhor integração
- Para produção, configure `developer_mode=0`
- Configure email para notificações
- Faça backups regulares do banco de dados
- Workers e scheduler devem rodar em serviços separados

## 🔗 Referências

- [Documentação do Frappe](https://frappeframework.com/docs)
- [Documentação do Frappe CRM](https://docs.frappe.io/crm)
- [Documentação do Insights](https://github.com/frappe/insights)
- [Documentação da Railway](https://docs.railway.app)

---

**Nota**: Este deploy é para o **Frappe Bench** (CRM + Insights). Para deploy da integração Google, veja `../google-crm-integration/RAILWAY_DEPLOY.md`

