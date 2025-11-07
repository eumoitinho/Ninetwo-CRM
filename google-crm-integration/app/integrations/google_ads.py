"""
Google Ads Integration

Client for interacting with Google Ads API to fetch campaign insights and leads.
"""

from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
from loguru import logger
from google.ads.googleads.client import GoogleAdsClient as GAdsClient
from google.ads.googleads.errors import GoogleAdsException

from app.config import settings
from app.models import GoogleAdsInsight


class GoogleAdsClient:
    """
    Client for interacting with Google Ads API.

    Fetches campaign performance data and lead form submissions.
    """

    def __init__(self, refresh_token: Optional[str] = None):
        """
        Initialize Google Ads client.

        Args:
            refresh_token: OAuth refresh token for the user
        """
        self.refresh_token = refresh_token or settings.google_ads_refresh_token
        self.client: Optional[GAdsClient] = None

    def _initialize_client(self):
        """Initialize Google Ads API client"""
        if self.client:
            return

        try:
            credentials = {
                "developer_token": settings.google_ads_developer_token,
                "client_id": settings.google_ads_client_id,
                "client_secret": settings.google_ads_client_secret,
                "refresh_token": self.refresh_token,
                "login_customer_id": settings.google_ads_login_customer_id,
                "use_proto_plus": True
            }

            self.client = GAdsClient.load_from_dict(credentials)
            logger.info("Initialized Google Ads client")

        except Exception as e:
            logger.error(f"Failed to initialize Google Ads client: {str(e)}")
            raise

    def get_campaign_performance(
        self,
        customer_id: str,
        start_date: date,
        end_date: date,
        user_id: str
    ) -> List[GoogleAdsInsight]:
        """
        Fetch campaign performance metrics.

        Args:
            customer_id: Google Ads customer ID
            start_date: Start date for the report
            end_date: End date for the report
            user_id: User ID for associating insights

        Returns:
            List of GoogleAdsInsight objects
        """
        self._initialize_client()

        try:
            ga_service = self.client.get_service("GoogleAdsService")

            # Build query for campaign performance
            query = f"""
                SELECT
                    customer.id,
                    campaign.id,
                    campaign.name,
                    segments.date,
                    metrics.impressions,
                    metrics.clicks,
                    metrics.cost_micros,
                    metrics.conversions,
                    metrics.conversions_value,
                    metrics.ctr,
                    metrics.average_cpc
                FROM campaign
                WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
                    AND campaign.status = 'ENABLED'
                ORDER BY segments.date DESC
            """

            # Execute query
            search_request = self.client.get_type("SearchGoogleAdsRequest")
            search_request.customer_id = customer_id.replace('-', '')
            search_request.query = query

            response = ga_service.search(request=search_request)

            insights = []
            for row in response:
                # Extract data from response
                insight = GoogleAdsInsight(
                    user_id=user_id,
                    customer_id=customer_id,
                    campaign_id=str(row.campaign.id),
                    campaign_name=row.campaign.name,
                    date=datetime.strptime(row.segments.date, '%Y-%m-%d').date(),
                    impressions=row.metrics.impressions,
                    clicks=row.metrics.clicks,
                    cost_micros=row.metrics.cost_micros,
                    conversions=row.metrics.conversions,
                    conversion_value=row.metrics.conversions_value,
                    ctr=row.metrics.ctr,
                    cpc_micros=row.metrics.average_cpc if hasattr(row.metrics, 'average_cpc') else 0
                )

                # Calculate conversion rate
                if insight.clicks > 0:
                    insight.conversion_rate = (insight.conversions / insight.clicks) * 100

                insights.append(insight)

            logger.info(f"Fetched {len(insights)} campaign insights for customer {customer_id}")
            return insights

        except GoogleAdsException as ex:
            logger.error(f"Google Ads API error: {ex}")
            for error in ex.failure.errors:
                logger.error(f"Error: {error.message}")
            raise

        except Exception as e:
            logger.error(f"Failed to fetch campaign performance: {str(e)}")
            raise

    def get_ad_group_performance(
        self,
        customer_id: str,
        campaign_id: str,
        start_date: date,
        end_date: date,
        user_id: str
    ) -> List[GoogleAdsInsight]:
        """
        Fetch ad group performance metrics.

        Args:
            customer_id: Google Ads customer ID
            campaign_id: Campaign ID to filter by
            start_date: Start date for the report
            end_date: End date for the report
            user_id: User ID for associating insights

        Returns:
            List of GoogleAdsInsight objects with ad group data
        """
        self._initialize_client()

        try:
            ga_service = self.client.get_service("GoogleAdsService")

            query = f"""
                SELECT
                    customer.id,
                    campaign.id,
                    campaign.name,
                    ad_group.id,
                    ad_group.name,
                    segments.date,
                    metrics.impressions,
                    metrics.clicks,
                    metrics.cost_micros,
                    metrics.conversions,
                    metrics.conversions_value,
                    metrics.ctr,
                    metrics.average_cpc
                FROM ad_group
                WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
                    AND campaign.id = {campaign_id}
                    AND ad_group.status = 'ENABLED'
                ORDER BY segments.date DESC
            """

            search_request = self.client.get_type("SearchGoogleAdsRequest")
            search_request.customer_id = customer_id.replace('-', '')
            search_request.query = query

            response = ga_service.search(request=search_request)

            insights = []
            for row in response:
                insight = GoogleAdsInsight(
                    user_id=user_id,
                    customer_id=customer_id,
                    campaign_id=str(row.campaign.id),
                    campaign_name=row.campaign.name,
                    date=datetime.strptime(row.segments.date, '%Y-%m-%d').date(),
                    impressions=row.metrics.impressions,
                    clicks=row.metrics.clicks,
                    cost_micros=row.metrics.cost_micros,
                    conversions=row.metrics.conversions,
                    conversion_value=row.metrics.conversions_value,
                    ctr=row.metrics.ctr,
                    cpc_micros=row.metrics.average_cpc if hasattr(row.metrics, 'average_cpc') else 0,
                    ad_group_id=str(row.ad_group.id),
                    ad_group_name=row.ad_group.name
                )

                if insight.clicks > 0:
                    insight.conversion_rate = (insight.conversions / insight.clicks) * 100

                insights.append(insight)

            logger.info(f"Fetched {len(insights)} ad group insights for campaign {campaign_id}")
            return insights

        except GoogleAdsException as ex:
            logger.error(f"Google Ads API error: {ex}")
            raise

        except Exception as e:
            logger.error(f"Failed to fetch ad group performance: {str(e)}")
            raise

    def get_lead_form_submissions(
        self,
        customer_id: str,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Fetch lead form submissions from Google Ads.

        Args:
            customer_id: Google Ads customer ID
            start_date: Start date for fetching leads
            end_date: End date for fetching leads

        Returns:
            List of lead dictionaries
        """
        self._initialize_client()

        try:
            ga_service = self.client.get_service("GoogleAdsService")

            # Query for lead form extensions and submissions
            query = f"""
                SELECT
                    lead_form_submission_data.id,
                    lead_form_submission_data.asset_id,
                    lead_form_submission_data.campaign_id,
                    lead_form_submission_data.ad_group_id,
                    lead_form_submission_data.gclid,
                    lead_form_submission_data.submission_date_time,
                    lead_form_submission_field.field_value
                FROM lead_form_submission_data
                WHERE lead_form_submission_data.submission_date_time BETWEEN '{start_date}' AND '{end_date}'
                ORDER BY lead_form_submission_data.submission_date_time DESC
            """

            search_request = self.client.get_type("SearchGoogleAdsRequest")
            search_request.customer_id = customer_id.replace('-', '')
            search_request.query = query

            response = ga_service.search(request=search_request)

            leads = []
            for row in response:
                lead_data = {
                    'id': row.lead_form_submission_data.id,
                    'asset_id': row.lead_form_submission_data.asset_id,
                    'campaign_id': str(row.lead_form_submission_data.campaign_id),
                    'ad_group_id': str(row.lead_form_submission_data.ad_group_id),
                    'gclid': row.lead_form_submission_data.gclid,
                    'submission_datetime': row.lead_form_submission_data.submission_date_time,
                    'fields': {}
                }

                # Extract form fields
                if hasattr(row, 'lead_form_submission_field'):
                    lead_data['fields'][row.lead_form_submission_field.field_type] = \
                        row.lead_form_submission_field.field_value

                leads.append(lead_data)

            logger.info(f"Fetched {len(leads)} lead form submissions")
            return leads

        except GoogleAdsException as ex:
            logger.error(f"Google Ads API error when fetching leads: {ex}")
            # Lead form data might not be available for all accounts
            logger.warning("Lead form submissions may not be available for this account")
            return []

        except Exception as e:
            logger.error(f"Failed to fetch lead form submissions: {str(e)}")
            raise


# Example usage
if __name__ == "__main__":
    # This is for testing purposes
    client = GoogleAdsClient()
    today = date.today()
    start = today - timedelta(days=30)

    # Fetch campaign performance
    insights = client.get_campaign_performance(
        customer_id=settings.google_ads_login_customer_id,
        start_date=start,
        end_date=today,
        user_id="test_user"
    )

    for insight in insights[:5]:  # Print first 5
        print(f"Campaign: {insight.campaign_name}, Clicks: {insight.clicks}, Cost: ${insight.cost}")
