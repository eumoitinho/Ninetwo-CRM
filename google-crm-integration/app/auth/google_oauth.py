"""
Google OAuth Handler

Handles OAuth 2.0 authentication flow with Google.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from loguru import logger
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from app.config import settings


class GoogleOAuthHandler:
    """
    Handler for Google OAuth 2.0 authentication flow.

    Manages the OAuth flow for obtaining and refreshing access tokens
    for Google Ads and Google Analytics APIs.
    """

    # OAuth scopes required for Google Ads and Analytics
    SCOPES = [
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile',
        'https://www.googleapis.com/auth/adwords',  # Google Ads
        'https://www.googleapis.com/auth/analytics.readonly',  # Google Analytics (read)
    ]

    def __init__(self):
        """Initialize OAuth handler"""
        self.client_config = {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.google_redirect_uri],
            }
        }

    def get_authorization_url(
        self,
        state: Optional[str] = None,
        scopes: Optional[List[str]] = None
    ) -> tuple[str, str]:
        """
        Generate authorization URL for OAuth flow.

        Args:
            state: Optional state parameter for CSRF protection
            scopes: Optional custom scopes (defaults to SCOPES)

        Returns:
            Tuple of (authorization_url, state)
        """
        try:
            flow = Flow.from_client_config(
                client_config=self.client_config,
                scopes=scopes or self.SCOPES,
                redirect_uri=settings.google_redirect_uri
            )

            authorization_url, state = flow.authorization_url(
                access_type='offline',  # Request refresh token
                include_granted_scopes='true',  # Incremental authorization
                state=state,
                prompt='consent'  # Force consent screen to get refresh token
            )

            logger.info("Generated OAuth authorization URL")
            return authorization_url, state

        except Exception as e:
            logger.error(f"Failed to generate authorization URL: {str(e)}")
            raise

    def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens.

        Args:
            code: Authorization code from OAuth callback

        Returns:
            Dictionary containing token information
        """
        try:
            flow = Flow.from_client_config(
                client_config=self.client_config,
                scopes=self.SCOPES,
                redirect_uri=settings.google_redirect_uri
            )

            # Exchange code for tokens
            flow.fetch_token(code=code)

            credentials = flow.credentials

            # Calculate token expiry
            expires_at = None
            if credentials.expiry:
                expires_at = credentials.expiry
            elif credentials.expires_in:
                expires_at = datetime.utcnow() + timedelta(seconds=credentials.expires_in)

            token_info = {
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_expires_at': expires_at,
                'scopes': credentials.scopes or self.SCOPES,
            }

            logger.info("Successfully exchanged code for tokens")
            return token_info

        except Exception as e:
            logger.error(f"Failed to exchange code for tokens: {str(e)}")
            raise

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token

        Returns:
            Dictionary containing new token information
        """
        try:
            credentials = Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.google_client_id,
                client_secret=settings.google_client_secret,
                scopes=self.SCOPES
            )

            # Refresh the token
            request = Request()
            credentials.refresh(request)

            # Calculate token expiry
            expires_at = None
            if credentials.expiry:
                expires_at = credentials.expiry
            elif credentials.expires_in:
                expires_at = datetime.utcnow() + timedelta(seconds=credentials.expires_in)

            token_info = {
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token or refresh_token,
                'token_expires_at': expires_at,
                'scopes': credentials.scopes or self.SCOPES,
            }

            logger.info("Successfully refreshed access token")
            return token_info

        except Exception as e:
            logger.error(f"Failed to refresh access token: {str(e)}")
            raise

    def get_credentials(
        self,
        access_token: str,
        refresh_token: Optional[str] = None,
        token_expires_at: Optional[datetime] = None
    ) -> Credentials:
        """
        Create Google Credentials object.

        Args:
            access_token: Access token
            refresh_token: Optional refresh token
            token_expires_at: Optional token expiry datetime

        Returns:
            Google Credentials object
        """
        return Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            scopes=self.SCOPES,
            expiry=token_expires_at
        )

    def is_token_expired(self, token_expires_at: Optional[datetime]) -> bool:
        """
        Check if token is expired or will expire soon.

        Args:
            token_expires_at: Token expiry datetime

        Returns:
            True if token is expired or will expire within 5 minutes
        """
        if not token_expires_at:
            return True

        # Add 5 minute buffer
        buffer = timedelta(minutes=5)
        return datetime.utcnow() >= (token_expires_at - buffer)


# Global instance
google_oauth = GoogleOAuthHandler()
