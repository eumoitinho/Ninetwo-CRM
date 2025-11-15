# Guia de Deploy - Ninetwo CRM

Este projeto contém dois componentes principais que podem ser deployados separadamente:

## 📦 Componentes do Projeto

### 1. **Frappe Bench** (Sistema Principal)
**Localização**: `frappe-bench/`

Sistema base que gerencia os seguintes apps:
- **Frappe Framework**: Framework base
- **CRM**: Aplicativo de Customer Relationship Management
- **Insights**: Aplicativo de análise de dados
- **Library Management**: Gerenciamento de biblioteca (opcional)

**Tecnologias**:
- Python (Frappe Framework)
- MariaDB/MySQL
- Redis
- Node.js (para frontend)

**Documentação de Deploy**: [`frappe-bench/RAILWAY_DEPLOY.md`](./frappe-bench/RAILWAY_DEPLOY.md)

---

### 2. **Google CRM Integration** (Integração Adicional)
**Localização**: `google-crm-integration/`

API REST separada para integração com:
- Google Ads API
- Google Analytics (GA4)
- Couchbase Cloud (armazenamento)
- Confluent Cloud (Kafka - streaming)

**Tecnologias**:
- Python (FastAPI)
- Couchbase Cloud
- Confluent Cloud (Kafka)
- Redis (para Celery)

**Documentação de Deploy**: [`google-crm-integration/RAILWAY_DEPLOY.md`](./google-crm-integration/RAILWAY_DEPLOY.md)

---

## 🎯 Qual Deploy Fazer?

### Deploy do Frappe (CRM + Insights)
**Use quando**:
- Quer fazer deploy do sistema principal de CRM
- Precisa do sistema completo com interface web
- Quer gerenciar leads, deals, e análises

**Arquivos de deploy**:
- `frappe-bench/Dockerfile`
- `frappe-bench/railway.json`
- `frappe-bench/RAILWAY_DEPLOY.md`

### Deploy da Integração Google
**Use quando**:
- Já tem o Frappe CRM rodando
- Precisa integrar com Google Ads e Analytics
- Quer sincronizar dados do Google com o CRM

**Arquivos de deploy**:
- `google-crm-integration/Dockerfile`
- `google-crm-integration/railway.json`
- `google-crm-integration/RAILWAY_DEPLOY.md`

---

## 🚀 Deploy Completo (Ambos)

Para ter o sistema completo funcionando:

1. **Primeiro**: Deploy do Frappe Bench
   - Siga: [`frappe-bench/RAILWAY_DEPLOY.md`](./frappe-bench/RAILWAY_DEPLOY.md)
   - Isso cria o sistema principal de CRM

2. **Depois**: Deploy da Integração Google
   - Siga: [`google-crm-integration/RAILWAY_DEPLOY.md`](./google-crm-integration/RAILWAY_DEPLOY.md)
   - Isso adiciona a integração com Google Ads/Analytics

---

## 📋 Pré-requisitos Comuns

### Para Frappe Bench:
- ✅ Conta Railway
- ✅ MariaDB/MySQL (Railway pode provisionar)
- ✅ Redis (Railway pode provisionar)
- ✅ Repositório GitHub

### Para Google Integration:
- ✅ Conta Railway
- ✅ Couchbase Cloud
- ✅ Confluent Cloud (Kafka)
- ✅ Credenciais Google Cloud (OAuth, Ads, Analytics)
- ✅ Redis (opcional, para Celery)

---

## 🔗 Arquitetura

```
┌─────────────────────────────────────┐
│      Frappe Bench (CRM + Insights)   │
│  - Interface Web                     │
│  - Gerenciamento de Leads/Deals      │
│  - Análises e Relatórios             │
└──────────────┬──────────────────────┘
               │
               │ (API Integration)
               │
┌──────────────▼──────────────────────┐
│   Google CRM Integration (FastAPI)  │
│  - Google Ads API                    │
│  - Google Analytics                  │
│  - Couchbase (Storage)               │
│  - Kafka (Streaming)                 │
└─────────────────────────────────────┘
```

---

## 📝 Notas Importantes

1. **Ordem de Deploy**: Recomenda-se fazer deploy do Frappe primeiro, depois da integração Google
2. **Variáveis de Ambiente**: Cada componente tem suas próprias variáveis de ambiente
3. **Domínios**: Cada componente pode ter seu próprio domínio na Railway
4. **Comunicação**: A integração Google pode se comunicar com o Frappe via API

---

## 🆘 Suporte

- **Frappe Bench**: Veja [`frappe-bench/RAILWAY_DEPLOY.md`](./frappe-bench/RAILWAY_DEPLOY.md)
- **Google Integration**: Veja [`google-crm-integration/RAILWAY_DEPLOY.md`](./google-crm-integration/RAILWAY_DEPLOY.md)
- **Documentação Railway**: https://docs.railway.app

