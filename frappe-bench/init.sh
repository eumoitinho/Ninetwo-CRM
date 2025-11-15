#!/bin/bash
set -e

echo "=== Inicializando Frappe Bench ==="

# Verificar se o site já existe
SITE_NAME=${FRAPPE_SITE_NAME:-crm.localhost}
SITE_PATH="sites/${SITE_NAME}"

if [ ! -f "${SITE_PATH}/site_config.json" ]; then
    echo "Criando novo site: ${SITE_NAME}..."
    
    # Criar site
    bench new-site ${SITE_NAME} \
        --db-host ${DB_HOST} \
        --db-port ${DB_PORT} \
        --db-name ${DB_NAME} \
        --db-user ${DB_USER} \
        --db-password ${DB_PASSWORD} \
        --admin-password ${FRAPPE_ADMIN_PASSWORD} \
        --no-mariadb-socket \
        --install-app frappe \
        --install-app crm \
        --install-app insights
    
    echo "Site criado com sucesso!"
else
    echo "Site ${SITE_NAME} já existe, pulando criação..."
fi

# Build assets para todos os apps
echo "=== Building assets ==="
bench build --app frappe || true
bench build --app crm || true
bench build --app insights || true

# Migrar banco de dados
echo "=== Migrando banco de dados ==="
bench --site ${SITE_NAME} migrate || true

# Limpar cache
echo "=== Limpando cache ==="
bench --site ${SITE_NAME} clear-cache || true

# Configurações de produção
echo "=== Configurando ambiente de produção ==="
bench --site ${SITE_NAME} set-config developer_mode 0 || true
bench --site ${SITE_NAME} set-config mute_emails 0 || true

echo "=== Inicialização concluída! ==="

