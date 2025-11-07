"""
Couchbase Service

Service for managing Couchbase Cloud connections and operations.
"""

from typing import Optional, List, Dict, Any
from datetime import timedelta
from loguru import logger
from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions, QueryOptions
from couchbase.exceptions import DocumentNotFoundException, CouchbaseException
from couchbase.management.collections import CollectionSpec

from app.config import settings
from app.models import Lead, GoogleAdsInsight, GoogleAnalyticsInsight, User, GoogleOAuthConnection


class CouchbaseService:
    """
    Service class for interacting with Couchbase Cloud.

    Provides CRUD operations and query methods for all document types.
    """

    def __init__(self):
        """Initialize Couchbase connection"""
        self.cluster: Optional[Cluster] = None
        self.bucket = None
        self.scope = None
        self.collections: Dict[str, Any] = {}
        self._connected = False

    async def connect(self):
        """
        Establish connection to Couchbase Cloud.

        Raises:
            CouchbaseException: If connection fails
        """
        try:
            logger.info(f"Connecting to Couchbase Cloud: {settings.couchbase_connection_string}")

            # Create authenticator
            auth = PasswordAuthenticator(
                settings.couchbase_username,
                settings.couchbase_password
            )

            # Connect to cluster
            self.cluster = Cluster(
                settings.couchbase_connection_string,
                ClusterOptions(auth)
            )

            # Wait until cluster is ready
            self.cluster.wait_until_ready(timedelta(seconds=10))

            # Get bucket
            self.bucket = self.cluster.bucket(settings.couchbase_bucket_name)

            # Get scope
            self.scope = self.bucket.scope(settings.couchbase_scope_name)

            # Get collections
            self.collections = {
                'leads': self.scope.collection(settings.couchbase_collection_leads),
                'insights': self.scope.collection(settings.couchbase_collection_insights),
                'users': self.scope.collection(settings.couchbase_collection_users),
            }

            self._connected = True
            logger.info("Successfully connected to Couchbase Cloud")

        except Exception as e:
            logger.error(f"Failed to connect to Couchbase: {str(e)}")
            raise

    async def disconnect(self):
        """Disconnect from Couchbase Cloud"""
        if self.cluster:
            self.cluster.close()
            self._connected = False
            logger.info("Disconnected from Couchbase Cloud")

    def ensure_connected(self):
        """Ensure connection is established"""
        if not self._connected:
            raise RuntimeError("Not connected to Couchbase. Call connect() first.")

    # ===== Lead Operations =====

    async def create_lead(self, lead: Lead) -> Lead:
        """
        Create a new lead.

        Args:
            lead: Lead object to create

        Returns:
            Created lead with ID
        """
        self.ensure_connected()

        try:
            collection = self.collections['leads']
            collection.upsert(lead.id, lead.model_dump())
            logger.info(f"Created lead: {lead.id}")
            return lead
        except Exception as e:
            logger.error(f"Failed to create lead: {str(e)}")
            raise

    async def get_lead(self, lead_id: str) -> Optional[Lead]:
        """
        Get a lead by ID.

        Args:
            lead_id: Lead ID

        Returns:
            Lead object or None if not found
        """
        self.ensure_connected()

        try:
            collection = self.collections['leads']
            result = collection.get(lead_id)
            return Lead(**result.content_as[dict])
        except DocumentNotFoundException:
            logger.warning(f"Lead not found: {lead_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to get lead: {str(e)}")
            raise

    async def update_lead(self, lead: Lead) -> Lead:
        """
        Update an existing lead.

        Args:
            lead: Lead object with updates

        Returns:
            Updated lead
        """
        self.ensure_connected()

        try:
            collection = self.collections['leads']
            collection.replace(lead.id, lead.model_dump())
            logger.info(f"Updated lead: {lead.id}")
            return lead
        except Exception as e:
            logger.error(f"Failed to update lead: {str(e)}")
            raise

    async def delete_lead(self, lead_id: str) -> bool:
        """
        Delete a lead.

        Args:
            lead_id: Lead ID

        Returns:
            True if deleted, False if not found
        """
        self.ensure_connected()

        try:
            collection = self.collections['leads']
            collection.remove(lead_id)
            logger.info(f"Deleted lead: {lead_id}")
            return True
        except DocumentNotFoundException:
            logger.warning(f"Lead not found for deletion: {lead_id}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete lead: {str(e)}")
            raise

    async def query_leads(self, filters: Dict[str, Any], limit: int = 100) -> List[Lead]:
        """
        Query leads with filters.

        Args:
            filters: Dictionary of field:value pairs to filter by
            limit: Maximum number of results

        Returns:
            List of matching leads
        """
        self.ensure_connected()

        try:
            # Build N1QL query
            where_clauses = []
            params = {}

            for key, value in filters.items():
                param_name = f"${key}"
                where_clauses.append(f"{key} = {param_name}")
                params[key] = value

            where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

            query = f"""
                SELECT leads.*
                FROM `{settings.couchbase_bucket_name}`.`{settings.couchbase_scope_name}`.`{settings.couchbase_collection_leads}` AS leads
                WHERE {where_clause} AND doc_type = 'lead'
                LIMIT {limit}
            """

            result = self.cluster.query(query, QueryOptions(named_parameters=params))

            leads = [Lead(**row['leads']) for row in result]
            logger.info(f"Found {len(leads)} leads matching filters")
            return leads

        except Exception as e:
            logger.error(f"Failed to query leads: {str(e)}")
            raise

    # ===== Insight Operations =====

    async def create_ads_insight(self, insight: GoogleAdsInsight) -> GoogleAdsInsight:
        """Create a Google Ads insight"""
        self.ensure_connected()

        try:
            collection = self.collections['insights']
            collection.upsert(insight.id, insight.model_dump())
            logger.info(f"Created Google Ads insight: {insight.id}")
            return insight
        except Exception as e:
            logger.error(f"Failed to create insight: {str(e)}")
            raise

    async def create_analytics_insight(self, insight: GoogleAnalyticsInsight) -> GoogleAnalyticsInsight:
        """Create a Google Analytics insight"""
        self.ensure_connected()

        try:
            collection = self.collections['insights']
            collection.upsert(insight.id, insight.model_dump())
            logger.info(f"Created Google Analytics insight: {insight.id}")
            return insight
        except Exception as e:
            logger.error(f"Failed to create insight: {str(e)}")
            raise

    async def get_insights_by_user(
        self,
        user_id: str,
        doc_type: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get insights for a specific user.

        Args:
            user_id: User ID
            doc_type: Type of insight ('google_ads_insight' or 'google_analytics_insight')
            limit: Maximum number of results

        Returns:
            List of insights
        """
        self.ensure_connected()

        try:
            query = f"""
                SELECT insights.*
                FROM `{settings.couchbase_bucket_name}`.`{settings.couchbase_scope_name}`.`{settings.couchbase_collection_insights}` AS insights
                WHERE user_id = $user_id AND doc_type = $doc_type
                ORDER BY date DESC
                LIMIT {limit}
            """

            result = self.cluster.query(
                query,
                QueryOptions(named_parameters={"user_id": user_id, "doc_type": doc_type})
            )

            insights = [row['insights'] for row in result]
            logger.info(f"Found {len(insights)} {doc_type} insights for user {user_id}")
            return insights

        except Exception as e:
            logger.error(f"Failed to query insights: {str(e)}")
            raise

    # ===== User Operations =====

    async def create_user(self, user: User) -> User:
        """Create a new user"""
        self.ensure_connected()

        try:
            collection = self.collections['users']
            collection.upsert(user.id, user.model_dump())
            logger.info(f"Created user: {user.id}")
            return user
        except Exception as e:
            logger.error(f"Failed to create user: {str(e)}")
            raise

    async def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID"""
        self.ensure_connected()

        try:
            collection = self.collections['users']
            result = collection.get(user_id)
            return User(**result.content_as[dict])
        except DocumentNotFoundException:
            logger.warning(f"User not found: {user_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to get user: {str(e)}")
            raise

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email"""
        self.ensure_connected()

        try:
            query = f"""
                SELECT users.*
                FROM `{settings.couchbase_bucket_name}`.`{settings.couchbase_scope_name}`.`{settings.couchbase_collection_users}` AS users
                WHERE email = $email AND doc_type = 'user'
                LIMIT 1
            """

            result = self.cluster.query(query, QueryOptions(named_parameters={"email": email}))

            rows = list(result)
            if rows:
                return User(**rows[0]['users'])
            return None

        except Exception as e:
            logger.error(f"Failed to get user by email: {str(e)}")
            raise

    async def create_oauth_connection(self, connection: GoogleOAuthConnection) -> GoogleOAuthConnection:
        """Create or update OAuth connection"""
        self.ensure_connected()

        try:
            collection = self.collections['users']
            collection.upsert(connection.id, connection.model_dump())
            logger.info(f"Created OAuth connection: {connection.id}")
            return connection
        except Exception as e:
            logger.error(f"Failed to create OAuth connection: {str(e)}")
            raise

    async def get_oauth_connection_by_user(self, user_id: str) -> Optional[GoogleOAuthConnection]:
        """Get active OAuth connection for a user"""
        self.ensure_connected()

        try:
            query = f"""
                SELECT oauth.*
                FROM `{settings.couchbase_bucket_name}`.`{settings.couchbase_scope_name}`.`{settings.couchbase_collection_users}` AS oauth
                WHERE user_id = $user_id AND doc_type = 'google_oauth_connection' AND is_active = true
                LIMIT 1
            """

            result = self.cluster.query(query, QueryOptions(named_parameters={"user_id": user_id}))

            rows = list(result)
            if rows:
                return GoogleOAuthConnection(**rows[0]['oauth'])
            return None

        except Exception as e:
            logger.error(f"Failed to get OAuth connection: {str(e)}")
            raise


# Global instance
couchbase_service = CouchbaseService()
