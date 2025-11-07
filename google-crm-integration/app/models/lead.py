"""
Lead Model

Represents a lead captured from Google Ads or other sources.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr
import uuid


class LeadSource(str, Enum):
    """Lead source enumeration"""
    GOOGLE_ADS = "google_ads"
    GOOGLE_ANALYTICS = "google_analytics"
    MANUAL = "manual"
    IMPORT = "import"
    API = "api"


class LeadStatus(str, Enum):
    """Lead status enumeration"""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    UNQUALIFIED = "unqualified"
    CONVERTED = "converted"
    LOST = "lost"


class Lead(BaseModel):
    """
    Lead model for storing lead information in Couchbase.

    This model represents a potential customer captured from various sources,
    primarily Google Ads Lead Forms.
    """

    # Unique identifier
    id: str = Field(default_factory=lambda: f"lead::{uuid.uuid4()}")

    # Basic Information
    name: str = Field(..., min_length=1, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=50)
    company: Optional[str] = Field(default=None, max_length=200)

    # Lead Details
    source: LeadSource = Field(default=LeadSource.MANUAL)
    status: LeadStatus = Field(default=LeadStatus.NEW)

    # Google Ads specific fields
    google_ads_campaign_id: Optional[str] = None
    google_ads_ad_group_id: Optional[str] = None
    google_ads_gclid: Optional[str] = None  # Google Click ID
    google_ads_form_id: Optional[str] = None

    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # User/Organization assignment
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    assigned_to: Optional[str] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    contacted_at: Optional[datetime] = None
    converted_at: Optional[datetime] = None

    # Notes
    notes: Optional[str] = None

    # Document type for Couchbase
    doc_type: str = Field(default="lead", const=True)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "lead::123e4567-e89b-12d3-a456-426614174000",
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "+1234567890",
                "company": "Acme Corp",
                "source": "google_ads",
                "status": "new",
                "google_ads_campaign_id": "1234567890",
                "google_ads_gclid": "Cj0KCQiA...",
                "metadata": {
                    "utm_source": "google",
                    "utm_medium": "cpc",
                    "utm_campaign": "summer_sale"
                }
            }
        }

    def dict(self, *args, **kwargs):
        """Override dict to convert datetime to ISO format"""
        d = super().model_dump(*args, **kwargs)

        # Convert datetime fields to ISO format strings
        for field in ['created_at', 'updated_at', 'contacted_at', 'converted_at']:
            if field in d and d[field] is not None:
                if isinstance(d[field], datetime):
                    d[field] = d[field].isoformat()

        return d
