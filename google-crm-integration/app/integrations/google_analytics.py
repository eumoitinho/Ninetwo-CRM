"""
Google Analytics Integration

Client for interacting with Google Analytics Data API (GA4) to fetch website insights.
"""

from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
from loguru import logger
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest,
    DateRange,
    Dimension,
    Metric,
    FilterExpression,
    Filter,
    OrderBy,
)
from google.oauth2.credentials import Credentials

from app.config import settings
from app.models import GoogleAnalyticsInsight


class GoogleAnalyticsClient:
    """
    Client for interacting with Google Analytics Data API (GA4).

    Fetches website analytics data including sessions, users, pageviews, and conversions.
    """

    def __init__(self, credentials: Optional[Credentials] = None):
        """
        Initialize Google Analytics client.

        Args:
            credentials: OAuth2 credentials for the user
        """
        self.credentials = credentials
        self.client: Optional[BetaAnalyticsDataClient] = None

    def _initialize_client(self):
        """Initialize Google Analytics Data API client"""
        if self.client:
            return

        try:
            if self.credentials:
                self.client = BetaAnalyticsDataClient(credentials=self.credentials)
            else:
                # Use application default credentials
                self.client = BetaAnalyticsDataClient()

            logger.info("Initialized Google Analytics client")

        except Exception as e:
            logger.error(f"Failed to initialize Google Analytics client: {str(e)}")
            raise

    def get_traffic_insights(
        self,
        property_id: str,
        start_date: date,
        end_date: date,
        user_id: str
    ) -> List[GoogleAnalyticsInsight]:
        """
        Fetch traffic insights including sessions, users, and pageviews.

        Args:
            property_id: Google Analytics property ID (format: "properties/12345")
            start_date: Start date for the report
            end_date: End date for the report
            user_id: User ID for associating insights

        Returns:
            List of GoogleAnalyticsInsight objects
        """
        self._initialize_client()

        try:
            # Build request
            request = RunReportRequest(
                property=f"properties/{property_id}",
                date_ranges=[DateRange(
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d')
                )],
                dimensions=[
                    Dimension(name="date"),
                    Dimension(name="sessionSource"),
                    Dimension(name="sessionMedium"),
                    Dimension(name="sessionCampaignName"),
                ],
                metrics=[
                    Metric(name="sessions"),
                    Metric(name="totalUsers"),
                    Metric(name="newUsers"),
                    Metric(name="screenPageViews"),
                    Metric(name="bounceRate"),
                    Metric(name="averageSessionDuration"),
                    Metric(name="engagedSessions"),
                    Metric(name="engagementRate"),
                ],
                limit=10000  # Maximum rows
            )

            # Run report
            response = self.client.run_report(request)

            insights = []
            for row in response.rows:
                # Parse dimension values
                report_date = datetime.strptime(row.dimension_values[0].value, '%Y%m%d').date()
                source = row.dimension_values[1].value
                medium = row.dimension_values[2].value
                campaign = row.dimension_values[3].value

                # Parse metric values
                sessions = int(row.metric_values[0].value)
                users = int(row.metric_values[1].value)
                new_users = int(row.metric_values[2].value)
                pageviews = int(row.metric_values[3].value)
                bounce_rate = float(row.metric_values[4].value)
                avg_session_duration = float(row.metric_values[5].value)
                engaged_sessions = int(row.metric_values[6].value)
                engagement_rate = float(row.metric_values[7].value)

                insight = GoogleAnalyticsInsight(
                    user_id=user_id,
                    property_id=property_id,
                    date=report_date,
                    source=source if source != "(not set)" else None,
                    medium=medium if medium != "(not set)" else None,
                    campaign=campaign if campaign != "(not set)" else None,
                    sessions=sessions,
                    users=users,
                    new_users=new_users,
                    pageviews=pageviews,
                    bounce_rate=bounce_rate,
                    avg_session_duration=avg_session_duration,
                    engaged_sessions=engaged_sessions,
                    engagement_rate=engagement_rate
                )

                insights.append(insight)

            logger.info(f"Fetched {len(insights)} traffic insights from GA4")
            return insights

        except Exception as e:
            logger.error(f"Failed to fetch traffic insights: {str(e)}")
            raise

    def get_conversion_insights(
        self,
        property_id: str,
        start_date: date,
        end_date: date,
        user_id: str
    ) -> List[GoogleAnalyticsInsight]:
        """
        Fetch conversion and revenue insights.

        Args:
            property_id: Google Analytics property ID
            start_date: Start date for the report
            end_date: End date for the report
            user_id: User ID for associating insights

        Returns:
            List of GoogleAnalyticsInsight objects with conversion data
        """
        self._initialize_client()

        try:
            request = RunReportRequest(
                property=f"properties/{property_id}",
                date_ranges=[DateRange(
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d')
                )],
                dimensions=[
                    Dimension(name="date"),
                    Dimension(name="sessionSource"),
                    Dimension(name="sessionMedium"),
                    Dimension(name="sessionCampaignName"),
                ],
                metrics=[
                    Metric(name="sessions"),
                    Metric(name="conversions"),
                    Metric(name="totalRevenue"),
                    Metric(name="ecommercePurchases"),
                ],
                limit=10000
            )

            response = self.client.run_report(request)

            insights = []
            for row in response.rows:
                report_date = datetime.strptime(row.dimension_values[0].value, '%Y%m%d').date()
                source = row.dimension_values[1].value
                medium = row.dimension_values[2].value
                campaign = row.dimension_values[3].value

                sessions = int(row.metric_values[0].value)
                conversions = float(row.metric_values[1].value)
                revenue = float(row.metric_values[2].value)
                transactions = int(row.metric_values[3].value)

                insight = GoogleAnalyticsInsight(
                    user_id=user_id,
                    property_id=property_id,
                    date=report_date,
                    source=source if source != "(not set)" else None,
                    medium=medium if medium != "(not set)" else None,
                    campaign=campaign if campaign != "(not set)" else None,
                    sessions=sessions,
                    goal_completions=int(conversions),
                    revenue=revenue,
                    transactions=transactions
                )

                insights.append(insight)

            logger.info(f"Fetched {len(insights)} conversion insights from GA4")
            return insights

        except Exception as e:
            logger.error(f"Failed to fetch conversion insights: {str(e)}")
            raise

    def get_page_insights(
        self,
        property_id: str,
        start_date: date,
        end_date: date,
        user_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch top pages by pageviews.

        Args:
            property_id: Google Analytics property ID
            start_date: Start date for the report
            end_date: End date for the report
            user_id: User ID for associating insights
            limit: Maximum number of pages to return

        Returns:
            List of page performance dictionaries
        """
        self._initialize_client()

        try:
            request = RunReportRequest(
                property=f"properties/{property_id}",
                date_ranges=[DateRange(
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d')
                )],
                dimensions=[
                    Dimension(name="pagePath"),
                    Dimension(name="pageTitle"),
                ],
                metrics=[
                    Metric(name="screenPageViews"),
                    Metric(name="averageSessionDuration"),
                    Metric(name="bounceRate"),
                ],
                order_bys=[
                    OrderBy(metric=OrderBy.MetricOrderBy(metric_name="screenPageViews"), desc=True)
                ],
                limit=limit
            )

            response = self.client.run_report(request)

            pages = []
            for row in response.rows:
                page_data = {
                    'page_path': row.dimension_values[0].value,
                    'page_title': row.dimension_values[1].value,
                    'pageviews': int(row.metric_values[0].value),
                    'avg_session_duration': float(row.metric_values[1].value),
                    'bounce_rate': float(row.metric_values[2].value),
                }
                pages.append(page_data)

            logger.info(f"Fetched {len(pages)} top pages from GA4")
            return pages

        except Exception as e:
            logger.error(f"Failed to fetch page insights: {str(e)}")
            raise

    def get_realtime_data(self, property_id: str) -> Dict[str, Any]:
        """
        Fetch real-time active users data.

        Args:
            property_id: Google Analytics property ID

        Returns:
            Dictionary with real-time metrics
        """
        self._initialize_client()

        try:
            from google.analytics.data_v1beta.types import RunRealtimeReportRequest

            request = RunRealtimeReportRequest(
                property=f"properties/{property_id}",
                metrics=[
                    Metric(name="activeUsers"),
                    Metric(name="screenPageViews"),
                ],
                dimensions=[
                    Dimension(name="country"),
                    Dimension(name="city"),
                ]
            )

            response = self.client.run_realtime_report(request)

            total_active_users = 0
            total_pageviews = 0
            locations = []

            for row in response.rows:
                country = row.dimension_values[0].value
                city = row.dimension_values[1].value
                active_users = int(row.metric_values[0].value)
                pageviews = int(row.metric_values[1].value)

                total_active_users += active_users
                total_pageviews += pageviews

                locations.append({
                    'country': country,
                    'city': city,
                    'active_users': active_users,
                    'pageviews': pageviews
                })

            realtime_data = {
                'total_active_users': total_active_users,
                'total_pageviews': total_pageviews,
                'top_locations': sorted(locations, key=lambda x: x['active_users'], reverse=True)[:10],
                'timestamp': datetime.utcnow().isoformat()
            }

            logger.info(f"Fetched real-time data: {total_active_users} active users")
            return realtime_data

        except Exception as e:
            logger.error(f"Failed to fetch real-time data: {str(e)}")
            raise

    def get_combined_insights(
        self,
        property_id: str,
        start_date: date,
        end_date: date,
        user_id: str
    ) -> List[GoogleAnalyticsInsight]:
        """
        Fetch combined traffic and conversion insights in one call.

        Args:
            property_id: Google Analytics property ID
            start_date: Start date for the report
            end_date: End date for the report
            user_id: User ID for associating insights

        Returns:
            List of GoogleAnalyticsInsight objects with all metrics
        """
        self._initialize_client()

        try:
            request = RunReportRequest(
                property=f"properties/{property_id}",
                date_ranges=[DateRange(
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d')
                )],
                dimensions=[
                    Dimension(name="date"),
                    Dimension(name="sessionSource"),
                    Dimension(name="sessionMedium"),
                    Dimension(name="sessionCampaignName"),
                ],
                metrics=[
                    Metric(name="sessions"),
                    Metric(name="totalUsers"),
                    Metric(name="newUsers"),
                    Metric(name="screenPageViews"),
                    Metric(name="bounceRate"),
                    Metric(name="averageSessionDuration"),
                    Metric(name="engagedSessions"),
                    Metric(name="engagementRate"),
                    Metric(name="conversions"),
                    Metric(name="totalRevenue"),
                    Metric(name="ecommercePurchases"),
                ],
                limit=10000
            )

            response = self.client.run_report(request)

            insights = []
            for row in response.rows:
                report_date = datetime.strptime(row.dimension_values[0].value, '%Y%m%d').date()
                source = row.dimension_values[1].value
                medium = row.dimension_values[2].value
                campaign = row.dimension_values[3].value

                insight = GoogleAnalyticsInsight(
                    user_id=user_id,
                    property_id=property_id,
                    date=report_date,
                    source=source if source != "(not set)" else None,
                    medium=medium if medium != "(not set)" else None,
                    campaign=campaign if campaign != "(not set)" else None,
                    sessions=int(row.metric_values[0].value),
                    users=int(row.metric_values[1].value),
                    new_users=int(row.metric_values[2].value),
                    pageviews=int(row.metric_values[3].value),
                    bounce_rate=float(row.metric_values[4].value),
                    avg_session_duration=float(row.metric_values[5].value),
                    engaged_sessions=int(row.metric_values[6].value),
                    engagement_rate=float(row.metric_values[7].value),
                    goal_completions=int(float(row.metric_values[8].value)),
                    revenue=float(row.metric_values[9].value),
                    transactions=int(row.metric_values[10].value)
                )

                insights.append(insight)

            logger.info(f"Fetched {len(insights)} combined insights from GA4")
            return insights

        except Exception as e:
            logger.error(f"Failed to fetch combined insights: {str(e)}")
            raise


# Example usage
if __name__ == "__main__":
    # This is for testing purposes
    client = GoogleAnalyticsClient()
    today = date.today()
    start = today - timedelta(days=7)

    # Fetch combined insights
    insights = client.get_combined_insights(
        property_id=settings.google_analytics_property_id,
        start_date=start,
        end_date=today,
        user_id="test_user"
    )

    for insight in insights[:5]:
        print(f"Date: {insight.date}, Sessions: {insight.sessions}, Revenue: ${insight.revenue}")
