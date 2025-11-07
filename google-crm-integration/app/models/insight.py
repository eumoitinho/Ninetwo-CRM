"""
Insight Models

Models for storing Google Ads and Google Analytics insights.
"""

from datetime import datetime, date
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import uuid


class GoogleAdsInsight(BaseModel):
    """
    Google Ads Insight model for storing campaign performance data.
    """

    # Unique identifier
    id: str = Field(default_factory=lambda: f"ads_insight::{uuid.uuid4()}")

    # User/Organization
    user_id: str = Field(..., description="User ID who owns this data")
    organization_id: Optional[str] = None

    # Campaign Information
    customer_id: str = Field(..., description="Google Ads customer ID")
    campaign_id: str = Field(..., description="Campaign ID")
    campaign_name: str = Field(..., description="Campaign name")

    # Date range
    date: date = Field(..., description="Date for this insight")

    # Metrics
    impressions: int = Field(default=0, description="Number of impressions")
    clicks: int = Field(default=0, description="Number of clicks")
    cost_micros: int = Field(default=0, description="Cost in micros (1/1,000,000 of currency)")
    conversions: float = Field(default=0.0, description="Number of conversions")
    conversion_value: float = Field(default=0.0, description="Total conversion value")

    # Calculated metrics
    ctr: float = Field(default=0.0, description="Click-through rate")
    cpc_micros: int = Field(default=0, description="Cost per click in micros")
    conversion_rate: float = Field(default=0.0, description="Conversion rate")

    # Additional data
    ad_group_id: Optional[str] = None
    ad_group_name: Optional[str] = None
    keyword: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Document type
    doc_type: str = Field(default="google_ads_insight", const=True)

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user::123",
                "customer_id": "1234567890",
                "campaign_id": "987654321",
                "campaign_name": "Summer Sale Campaign",
                "date": "2024-01-15",
                "impressions": 10000,
                "clicks": 250,
                "cost_micros": 50000000,
                "conversions": 12.5,
                "conversion_value": 1250.00,
                "ctr": 2.5,
                "cpc_micros": 200000
            }
        }

    @property
    def cost(self) -> float:
        """Convert cost from micros to currency units"""
        return self.cost_micros / 1_000_000

    @property
    def cpc(self) -> float:
        """Convert CPC from micros to currency units"""
        return self.cpc_micros / 1_000_000


class GoogleAnalyticsInsight(BaseModel):
    """
    Google Analytics Insight model for storing website analytics data.
    """

    # Unique identifier
    id: str = Field(default_factory=lambda: f"ga_insight::{uuid.uuid4()}")

    # User/Organization
    user_id: str = Field(..., description="User ID who owns this data")
    organization_id: Optional[str] = None

    # Property Information
    property_id: str = Field(..., description="Google Analytics property ID")

    # Date range
    date: date = Field(..., description="Date for this insight")

    # Dimensions
    source: Optional[str] = Field(default=None, description="Traffic source")
    medium: Optional[str] = Field(default=None, description="Traffic medium")
    campaign: Optional[str] = Field(default=None, description="Campaign name")
    page_path: Optional[str] = Field(default=None, description="Page path")

    # Metrics
    sessions: int = Field(default=0, description="Number of sessions")
    users: int = Field(default=0, description="Number of users")
    new_users: int = Field(default=0, description="Number of new users")
    pageviews: int = Field(default=0, description="Number of pageviews")
    bounce_rate: float = Field(default=0.0, description="Bounce rate")
    avg_session_duration: float = Field(default=0.0, description="Average session duration in seconds")

    # Conversion metrics
    goal_completions: int = Field(default=0, description="Number of goal completions")
    goal_value: float = Field(default=0.0, description="Total goal value")
    transactions: int = Field(default=0, description="Number of transactions")
    revenue: float = Field(default=0.0, description="Total revenue")

    # Engagement metrics
    engaged_sessions: int = Field(default=0, description="Number of engaged sessions")
    engagement_rate: float = Field(default=0.0, description="Engagement rate")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Document type
    doc_type: str = Field(default="google_analytics_insight", const=True)

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user::123",
                "property_id": "12345678",
                "date": "2024-01-15",
                "source": "google",
                "medium": "cpc",
                "campaign": "summer_sale",
                "sessions": 1500,
                "users": 1200,
                "new_users": 800,
                "pageviews": 4500,
                "bounce_rate": 45.5,
                "avg_session_duration": 180.5,
                "goal_completions": 75,
                "revenue": 5000.00
            }
        }


class AggregatedInsight(BaseModel):
    """
    Aggregated insight combining Google Ads and Analytics data.
    """

    id: str = Field(default_factory=lambda: f"aggregated_insight::{uuid.uuid4()}")
    user_id: str
    date_from: date
    date_to: date

    # Combined metrics
    total_impressions: int = 0
    total_clicks: int = 0
    total_cost: float = 0.0
    total_sessions: int = 0
    total_users: int = 0
    total_conversions: float = 0.0
    total_revenue: float = 0.0

    # ROI calculations
    roi: float = 0.0
    roas: float = 0.0  # Return on Ad Spend

    # Document type
    doc_type: str = Field(default="aggregated_insight", const=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)
