"""
User and OAuth Models

Models for user management and Google OAuth connections.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr
import uuid


class GoogleOAuthConnection(BaseModel):
    """
    Google OAuth Connection model for storing user's Google account connection.
    """

    # Unique identifier
    id: str = Field(default_factory=lambda: f"oauth::{uuid.uuid4()}")

    # User association
    user_id: str = Field(..., description="Associated user ID")

    # Google account info
    google_user_id: str = Field(..., description="Google user ID")
    email: EmailStr = Field(..., description="Google account email")

    # OAuth tokens
    access_token: str = Field(..., description="OAuth access token")
    refresh_token: Optional[str] = Field(default=None, description="OAuth refresh token")
    token_expires_at: Optional[datetime] = Field(default=None, description="Token expiration time")

    # Scopes granted
    scopes: list[str] = Field(default_factory=list, description="Granted OAuth scopes")

    # Status
    is_active: bool = Field(default=True, description="Whether connection is active")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_sync_at: Optional[datetime] = None

    # Document type
    doc_type: str = Field(default="google_oauth_connection", const=True)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "oauth::123e4567-e89b-12d3-a456-426614174000",
                "user_id": "user::456",
                "google_user_id": "1234567890",
                "email": "user@example.com",
                "access_token": "ya29.a0...",
                "refresh_token": "1//0g...",
                "scopes": [
                    "https://www.googleapis.com/auth/adwords",
                    "https://www.googleapis.com/auth/analytics.readonly"
                ],
                "is_active": True
            }
        }


class User(BaseModel):
    """
    User model for CRM users.
    """

    # Unique identifier
    id: str = Field(default_factory=lambda: f"user::{uuid.uuid4()}")

    # Basic information
    email: EmailStr = Field(..., description="User email")
    name: str = Field(..., min_length=1, max_length=200)

    # Organization
    organization_id: Optional[str] = None

    # Settings
    settings: Dict[str, Any] = Field(default_factory=dict)

    # Google integrations
    google_oauth_connection_id: Optional[str] = None
    google_ads_customer_id: Optional[str] = None
    google_analytics_property_id: Optional[str] = None

    # Status
    is_active: bool = Field(default=True)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = None

    # Document type
    doc_type: str = Field(default="user", const=True)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "user::123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "name": "John Doe",
                "organization_id": "org::456",
                "google_ads_customer_id": "1234567890",
                "google_analytics_property_id": "12345678",
                "is_active": True
            }
        }
