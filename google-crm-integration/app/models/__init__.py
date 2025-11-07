"""
Data Models

Pydantic models for data validation and Couchbase document structure.
"""

from .lead import Lead, LeadSource, LeadStatus
from .insight import GoogleAdsInsight, GoogleAnalyticsInsight
from .user import User, GoogleOAuthConnection

__all__ = [
    "Lead",
    "LeadSource",
    "LeadStatus",
    "GoogleAdsInsight",
    "GoogleAnalyticsInsight",
    "User",
    "GoogleOAuthConnection",
]
