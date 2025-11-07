"""
Authentication Routes

OAuth authentication endpoints for Google integration.
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from loguru import logger
from datetime import datetime

from app.auth.google_oauth import google_oauth
from app.services.couchbase_service import couchbase_service
from app.models import GoogleOAuthConnection, User

router = APIRouter(prefix="/auth", tags=["Authentication"])


class AuthURLResponse(BaseModel):
    """Response model for authorization URL"""
    authorization_url: str
    state: str


class OAuthCallbackResponse(BaseModel):
    """Response model for OAuth callback"""
    success: bool
    message: str
    user_id: str


@router.get("/google/authorize", response_model=AuthURLResponse)
async def get_google_auth_url(user_id: str = Query(..., description="User ID to link OAuth")):
    """
    Get Google OAuth authorization URL.

    Args:
        user_id: User ID to associate with OAuth connection

    Returns:
        Authorization URL and state
    """
    try:
        # Store user_id in state (in production, use encrypted state)
        state = f"{user_id}:{datetime.utcnow().timestamp()}"

        authorization_url, state = google_oauth.get_authorization_url(state=state)

        logger.info(f"Generated OAuth URL for user {user_id}")

        return AuthURLResponse(
            authorization_url=authorization_url,
            state=state
        )

    except Exception as e:
        logger.error(f"Failed to generate auth URL: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/google/callback", response_model=OAuthCallbackResponse)
async def google_oauth_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: str = Query(..., description="State parameter for CSRF protection")
):
    """
    Handle OAuth callback from Google.

    Args:
        code: Authorization code
        state: State parameter (contains user_id)

    Returns:
        Success response with user_id
    """
    try:
        # Extract user_id from state (in production, decrypt and validate)
        user_id = state.split(':')[0]

        logger.info(f"Processing OAuth callback for user {user_id}")

        # Exchange code for tokens
        token_info = google_oauth.exchange_code_for_tokens(code)

        # Create or update OAuth connection
        oauth_connection = GoogleOAuthConnection(
            user_id=user_id,
            google_user_id=user_id,  # Get actual Google user ID from token
            email="user@example.com",  # Get from Google user info endpoint
            access_token=token_info['access_token'],
            refresh_token=token_info['refresh_token'],
            token_expires_at=token_info['token_expires_at'],
            scopes=token_info['scopes'],
            is_active=True
        )

        # Save to Couchbase
        await couchbase_service.create_oauth_connection(oauth_connection)

        logger.info(f"OAuth connection created for user {user_id}")

        return OAuthCallbackResponse(
            success=True,
            message="OAuth connection established successfully",
            user_id=user_id
        )

    except Exception as e:
        logger.error(f"OAuth callback failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OAuth callback failed: {str(e)}")


@router.delete("/google/disconnect/{user_id}")
async def disconnect_google_oauth(user_id: str):
    """
    Disconnect Google OAuth for a user.

    Args:
        user_id: User ID

    Returns:
        Success message
    """
    try:
        oauth_conn = await couchbase_service.get_oauth_connection_by_user(user_id)

        if not oauth_conn:
            raise HTTPException(status_code=404, detail="OAuth connection not found")

        # Deactivate connection
        oauth_conn.is_active = False
        oauth_conn.updated_at = datetime.utcnow()

        await couchbase_service.create_oauth_connection(oauth_conn)

        logger.info(f"Disconnected OAuth for user {user_id}")

        return {"success": True, "message": "OAuth connection disconnected"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disconnect OAuth: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
