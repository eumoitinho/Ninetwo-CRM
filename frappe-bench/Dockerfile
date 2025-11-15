# Dockerfile for Frappe Bench (CRM + Insights)
FROM frappe/bench:latest

# Set working directory
WORKDIR /home/frappe

# Copy bench configuration
COPY Procfile ./Procfile
COPY sites/common_site_config.json ./sites/common_site_config.json
COPY sites/apps.txt ./sites/apps.txt

# Copy initialization script
COPY init.sh ./init.sh
RUN chmod +x ./init.sh

# Expose ports
# Railway will provide PORT via environment variable
EXPOSE 8000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/api/method/ping || exit 1

# Start command - Railway provides PORT
# Run initialization script on first start, then serve
CMD sh -c "./init.sh && bench serve --port ${PORT:-8000} --host 0.0.0.0"

