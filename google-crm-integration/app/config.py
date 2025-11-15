"""
Application Configuration

Centralized configuration management using Pydantic Settings.
All settings are loaded from environment variables.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, model_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application Settings
    app_name: str = Field(default="Google CRM Integration", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    # Railway provides PORT, fallback to APP_PORT or 8080
    app_port: int = Field(default=8080)
    debug: bool = Field(default=True, alias="DEBUG")
    secret_key: str = Field(..., alias="SECRET_KEY")

    @model_validator(mode='after')
    def get_port(self):
        """Get PORT from Railway or APP_PORT, fallback to default"""
        # Railway provides PORT, check it first
        port = os.getenv('PORT') or os.getenv('APP_PORT')
        if port:
            self.app_port = int(port)
        return self

    # Google OAuth Configuration
    google_client_id: str = Field(..., alias="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(..., alias="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = Field(..., alias="GOOGLE_REDIRECT_URI")

    # Google Ads API
    google_ads_developer_token: str = Field(..., alias="GOOGLE_ADS_DEVELOPER_TOKEN")
    google_ads_client_id: str = Field(..., alias="GOOGLE_ADS_CLIENT_ID")
    google_ads_client_secret: str = Field(..., alias="GOOGLE_ADS_CLIENT_SECRET")
    google_ads_refresh_token: Optional[str] = Field(default=None, alias="GOOGLE_ADS_REFRESH_TOKEN")
    google_ads_login_customer_id: str = Field(..., alias="GOOGLE_ADS_LOGIN_CUSTOMER_ID")

    # Google Analytics API
    google_analytics_property_id: str = Field(..., alias="GOOGLE_ANALYTICS_PROPERTY_ID")

    # Couchbase Cloud Configuration
    couchbase_connection_string: str = Field(..., alias="COUCHBASE_CONNECTION_STRING")
    couchbase_username: str = Field(..., alias="COUCHBASE_USERNAME")
    couchbase_password: str = Field(..., alias="COUCHBASE_PASSWORD")
    couchbase_bucket_name: str = Field(default="crm-data", alias="COUCHBASE_BUCKET_NAME")
    couchbase_scope_name: str = Field(default="crm", alias="COUCHBASE_SCOPE_NAME")
    couchbase_collection_leads: str = Field(default="leads", alias="COUCHBASE_COLLECTION_LEADS")
    couchbase_collection_insights: str = Field(default="insights", alias="COUCHBASE_COLLECTION_INSIGHTS")
    couchbase_collection_users: str = Field(default="users", alias="COUCHBASE_COLLECTION_USERS")

    # Confluent Kafka (Cloud) Configuration
    kafka_bootstrap_servers: str = Field(..., alias="KAFKA_BOOTSTRAP_SERVERS")
    kafka_sasl_username: str = Field(..., alias="KAFKA_SASL_USERNAME")
    kafka_sasl_password: str = Field(..., alias="KAFKA_SASL_PASSWORD")
    kafka_security_protocol: str = Field(default="SASL_SSL", alias="KAFKA_SECURITY_PROTOCOL")
    kafka_sasl_mechanism: str = Field(default="PLAIN", alias="KAFKA_SASL_MECHANISM")
    kafka_topic_leads: str = Field(default="crm.leads", alias="KAFKA_TOPIC_LEADS")
    kafka_topic_insights: str = Field(default="crm.insights", alias="KAFKA_TOPIC_INSIGHTS")
    kafka_topic_events: str = Field(default="crm.events", alias="KAFKA_TOPIC_EVENTS")

    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    redis_cache_ttl: int = Field(default=3600, alias="REDIS_CACHE_TTL")

    # Celery Configuration
    celery_broker_url: str = Field(default="redis://localhost:6379/1", alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/2", alias="CELERY_RESULT_BACKEND")

    # Sync Settings
    sync_interval_minutes: int = Field(default=15, alias="SYNC_INTERVAL_MINUTES")
    sync_days_lookback: int = Field(default=30, alias="SYNC_DAYS_LOOKBACK")

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
