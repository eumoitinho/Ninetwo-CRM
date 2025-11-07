"""
Insight Routes

Endpoints for fetching Google Ads and Analytics insights.
"""

from typing import List
from datetime import date, timedelta
from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from app.services.couchbase_service import couchbase_service
from app.services.sync_service import sync_service

router = APIRouter(prefix="/insights", tags=["Insights"])


@router.post("/sync/{user_id}")
async def sync_insights(
    user_id: str,
    days_back: int = Query(30, ge=1, le=90, description="Number of days to sync")
):
    """
    Trigger data sync for a user.

    Args:
        user_id: User ID
        days_back: Number of days to look back

    Returns:
        Sync results
    """
    try:
        logger.info(f"Triggering sync for user {user_id}")

        results = await sync_service.sync_user_data(user_id, days_back=days_back)

        return {
            "success": True,
            "message": "Data sync completed",
            "results": results
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Sync failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/google-ads/{user_id}")
async def get_google_ads_insights(
    user_id: str,
    limit: int = Query(100, ge=1, le=1000, description="Maximum results")
):
    """
    Get Google Ads insights for a user.

    Args:
        user_id: User ID
        limit: Maximum results

    Returns:
        List of Google Ads insights
    """
    try:
        insights = await couchbase_service.get_insights_by_user(
            user_id=user_id,
            doc_type='google_ads_insight',
            limit=limit
        )

        logger.info(f"Retrieved {len(insights)} Google Ads insights for user {user_id}")

        return {
            "success": True,
            "count": len(insights),
            "insights": insights
        }

    except Exception as e:
        logger.error(f"Failed to get insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/google-analytics/{user_id}")
async def get_google_analytics_insights(
    user_id: str,
    limit: int = Query(100, ge=1, le=1000, description="Maximum results")
):
    """
    Get Google Analytics insights for a user.

    Args:
        user_id: User ID
        limit: Maximum results

    Returns:
        List of Google Analytics insights
    """
    try:
        insights = await couchbase_service.get_insights_by_user(
            user_id=user_id,
            doc_type='google_analytics_insight',
            limit=limit
        )

        logger.info(f"Retrieved {len(insights)} Google Analytics insights for user {user_id}")

        return {
            "success": True,
            "count": len(insights),
            "insights": insights
        }

    except Exception as e:
        logger.error(f"Failed to get insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary/{user_id}")
async def get_insights_summary(
    user_id: str,
    days: int = Query(30, ge=1, le=90, description="Number of days for summary")
):
    """
    Get aggregated insights summary for a user.

    Args:
        user_id: User ID
        days: Number of days to aggregate

    Returns:
        Aggregated metrics summary
    """
    try:
        # Fetch both types of insights
        ads_insights = await couchbase_service.get_insights_by_user(
            user_id=user_id,
            doc_type='google_ads_insight',
            limit=1000
        )

        analytics_insights = await couchbase_service.get_insights_by_user(
            user_id=user_id,
            doc_type='google_analytics_insight',
            limit=1000
        )

        # Calculate aggregated metrics
        total_impressions = sum(i.get('impressions', 0) for i in ads_insights)
        total_clicks = sum(i.get('clicks', 0) for i in ads_insights)
        total_cost = sum(i.get('cost_micros', 0) / 1_000_000 for i in ads_insights)
        total_conversions = sum(i.get('conversions', 0) for i in ads_insights)

        total_sessions = sum(i.get('sessions', 0) for i in analytics_insights)
        total_users = sum(i.get('users', 0) for i in analytics_insights)
        total_revenue = sum(i.get('revenue', 0) for i in analytics_insights)

        # Calculate ROI and ROAS
        roi = ((total_revenue - total_cost) / total_cost * 100) if total_cost > 0 else 0
        roas = (total_revenue / total_cost) if total_cost > 0 else 0

        summary = {
            "user_id": user_id,
            "period_days": days,
            "google_ads": {
                "impressions": total_impressions,
                "clicks": total_clicks,
                "cost": round(total_cost, 2),
                "conversions": round(total_conversions, 2),
                "ctr": round((total_clicks / total_impressions * 100) if total_impressions > 0 else 0, 2),
                "cpc": round((total_cost / total_clicks) if total_clicks > 0 else 0, 2)
            },
            "google_analytics": {
                "sessions": total_sessions,
                "users": total_users,
                "revenue": round(total_revenue, 2)
            },
            "performance": {
                "roi_percentage": round(roi, 2),
                "roas": round(roas, 2)
            }
        }

        logger.info(f"Generated insights summary for user {user_id}")

        return {
            "success": True,
            "summary": summary
        }

    except Exception as e:
        logger.error(f"Failed to generate summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
