"""
Data Sync Service

Service for synchronizing data from Google Ads and Analytics to Couchbase and Kafka.
"""

from typing import Optional
from datetime import date, datetime, timedelta
from loguru import logger

from app.config import settings
from app.models import Lead, LeadSource, LeadStatus
from app.services.couchbase_service import couchbase_service
from app.services.kafka_service import kafka_service
from app.integrations.google_ads import GoogleAdsClient
from app.integrations.google_analytics import GoogleAnalyticsClient
from app.auth.google_oauth import google_oauth


class SyncService:
    """
    Service for synchronizing Google Ads and Analytics data.

    Orchestrates data collection from Google APIs and storage in Couchbase/Kafka.
    """

    async def sync_user_data(
        self,
        user_id: str,
        days_back: Optional[int] = None
    ) -> dict:
        """
        Sync all data for a user.

        Args:
            user_id: User ID to sync data for
            days_back: Number of days to look back (defaults to settings)

        Returns:
            Dictionary with sync results
        """
        try:
            logger.info(f"Starting data sync for user {user_id}")

            # Get user from Couchbase
            user = await couchbase_service.get_user(user_id)
            if not user:
                raise ValueError(f"User not found: {user_id}")

            # Get OAuth connection
            oauth_conn = await couchbase_service.get_oauth_connection_by_user(user_id)
            if not oauth_conn or not oauth_conn.is_active:
                raise ValueError(f"No active OAuth connection for user {user_id}")

            # Check if token needs refresh
            if google_oauth.is_token_expired(oauth_conn.token_expires_at):
                logger.info("Access token expired, refreshing...")
                token_info = google_oauth.refresh_access_token(oauth_conn.refresh_token)

                # Update OAuth connection
                oauth_conn.access_token = token_info['access_token']
                oauth_conn.refresh_token = token_info.get('refresh_token', oauth_conn.refresh_token)
                oauth_conn.token_expires_at = token_info['token_expires_at']
                oauth_conn.updated_at = datetime.utcnow()

                await couchbase_service.create_oauth_connection(oauth_conn)

            # Calculate date range
            days = days_back or settings.sync_days_lookback
            end_date = date.today()
            start_date = end_date - timedelta(days=days)

            results = {
                'user_id': user_id,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'ads_insights': 0,
                'analytics_insights': 0,
                'leads': 0,
                'errors': []
            }

            # Sync Google Ads data
            if user.google_ads_customer_id:
                try:
                    ads_results = await self.sync_google_ads_data(
                        user_id=user_id,
                        customer_id=user.google_ads_customer_id,
                        refresh_token=oauth_conn.refresh_token,
                        start_date=start_date,
                        end_date=end_date
                    )
                    results['ads_insights'] = ads_results['insights_count']
                    results['leads'] = ads_results['leads_count']
                except Exception as e:
                    logger.error(f"Failed to sync Google Ads data: {str(e)}")
                    results['errors'].append(f"Google Ads: {str(e)}")

            # Sync Google Analytics data
            if user.google_analytics_property_id:
                try:
                    credentials = google_oauth.get_credentials(
                        access_token=oauth_conn.access_token,
                        refresh_token=oauth_conn.refresh_token,
                        token_expires_at=oauth_conn.token_expires_at
                    )

                    analytics_results = await self.sync_google_analytics_data(
                        user_id=user_id,
                        property_id=user.google_analytics_property_id,
                        credentials=credentials,
                        start_date=start_date,
                        end_date=end_date
                    )
                    results['analytics_insights'] = analytics_results['insights_count']
                except Exception as e:
                    logger.error(f"Failed to sync Google Analytics data: {str(e)}")
                    results['errors'].append(f"Google Analytics: {str(e)}")

            # Update last sync time
            oauth_conn.last_sync_at = datetime.utcnow()
            await couchbase_service.create_oauth_connection(oauth_conn)

            logger.info(f"Data sync completed for user {user_id}: {results}")
            return results

        except Exception as e:
            logger.error(f"Failed to sync user data: {str(e)}")
            raise

    async def sync_google_ads_data(
        self,
        user_id: str,
        customer_id: str,
        refresh_token: str,
        start_date: date,
        end_date: date
    ) -> dict:
        """
        Sync Google Ads campaign performance and leads.

        Args:
            user_id: User ID
            customer_id: Google Ads customer ID
            refresh_token: OAuth refresh token
            start_date: Start date
            end_date: End date

        Returns:
            Dictionary with sync results
        """
        logger.info(f"Syncing Google Ads data for customer {customer_id}")

        # Initialize Google Ads client
        ads_client = GoogleAdsClient(refresh_token=refresh_token)

        # Fetch campaign performance
        insights = ads_client.get_campaign_performance(
            customer_id=customer_id,
            start_date=start_date,
            end_date=end_date,
            user_id=user_id
        )

        # Store insights in Couchbase and produce to Kafka
        for insight in insights:
            # Save to Couchbase
            await couchbase_service.create_ads_insight(insight)

            # Produce to Kafka
            kafka_service.produce_insight_event(
                insight=insight.model_dump(),
                event_type='google_ads_insight.created'
            )

        # Fetch lead form submissions
        lead_data = ads_client.get_lead_form_submissions(
            customer_id=customer_id,
            start_date=start_date,
            end_date=end_date
        )

        # Convert to Lead objects and store
        leads_created = 0
        for lead_info in lead_data:
            lead = Lead(
                name=lead_info['fields'].get('FULL_NAME', 'Unknown'),
                email=lead_info['fields'].get('EMAIL'),
                phone=lead_info['fields'].get('PHONE_NUMBER'),
                source=LeadSource.GOOGLE_ADS,
                status=LeadStatus.NEW,
                google_ads_campaign_id=lead_info['campaign_id'],
                google_ads_ad_group_id=lead_info['ad_group_id'],
                google_ads_gclid=lead_info['gclid'],
                google_ads_form_id=lead_info['asset_id'],
                user_id=user_id,
                metadata=lead_info
            )

            # Save to Couchbase
            await couchbase_service.create_lead(lead)

            # Produce to Kafka
            kafka_service.produce_lead_event(
                lead=lead.model_dump(),
                event_type='lead.created'
            )

            leads_created += 1

        logger.info(f"Synced {len(insights)} insights and {leads_created} leads from Google Ads")

        return {
            'insights_count': len(insights),
            'leads_count': leads_created
        }

    async def sync_google_analytics_data(
        self,
        user_id: str,
        property_id: str,
        credentials,
        start_date: date,
        end_date: date
    ) -> dict:
        """
        Sync Google Analytics insights.

        Args:
            user_id: User ID
            property_id: GA4 property ID
            credentials: OAuth credentials
            start_date: Start date
            end_date: End date

        Returns:
            Dictionary with sync results
        """
        logger.info(f"Syncing Google Analytics data for property {property_id}")

        # Initialize Google Analytics client
        analytics_client = GoogleAnalyticsClient(credentials=credentials)

        # Fetch combined insights
        insights = analytics_client.get_combined_insights(
            property_id=property_id,
            start_date=start_date,
            end_date=end_date,
            user_id=user_id
        )

        # Store insights in Couchbase and produce to Kafka
        for insight in insights:
            # Save to Couchbase
            await couchbase_service.create_analytics_insight(insight)

            # Produce to Kafka
            kafka_service.produce_insight_event(
                insight=insight.model_dump(),
                event_type='google_analytics_insight.created'
            )

        logger.info(f"Synced {len(insights)} insights from Google Analytics")

        return {
            'insights_count': len(insights)
        }


# Global instance
sync_service = SyncService()
