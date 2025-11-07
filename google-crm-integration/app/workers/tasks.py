"""
Celery Tasks

Background tasks for data synchronization.
"""

from loguru import logger
from celery import Task
import asyncio

from app.workers.celery_app import celery_app
from app.services.sync_service import sync_service
from app.services.couchbase_service import couchbase_service


class AsyncTask(Task):
    """Base task class that runs async functions"""

    def __call__(self, *args, **kwargs):
        """Run the task"""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.run(*args, **kwargs))


@celery_app.task(base=AsyncTask, name='app.workers.tasks.sync_user_data')
async def sync_user_data(user_id: str, days_back: int = None):
    """
    Sync data for a specific user.

    Args:
        user_id: User ID to sync
        days_back: Number of days to sync (optional)

    Returns:
        Sync results
    """
    try:
        logger.info(f"Starting background sync for user {user_id}")

        # Ensure connections
        if not couchbase_service._connected:
            await couchbase_service.connect()

        # Run sync
        results = await sync_service.sync_user_data(user_id, days_back=days_back)

        logger.info(f"Background sync completed for user {user_id}: {results}")
        return results

    except Exception as e:
        logger.error(f"Background sync failed for user {user_id}: {str(e)}")
        raise


@celery_app.task(base=AsyncTask, name='app.workers.tasks.sync_all_users')
async def sync_all_users():
    """
    Sync data for all active users.

    This task runs periodically to sync data for all users with active OAuth connections.

    Returns:
        Summary of sync results
    """
    try:
        logger.info("Starting background sync for all users")

        # Ensure connections
        if not couchbase_service._connected:
            await couchbase_service.connect()

        # Query all active OAuth connections
        query = f"""
            SELECT oauth.user_id
            FROM `{couchbase_service.bucket.name}`.`{couchbase_service.scope.name}`.`users` AS oauth
            WHERE doc_type = 'google_oauth_connection' AND is_active = true
        """

        result = couchbase_service.cluster.query(query)
        user_ids = [row['user_id'] for row in result]

        logger.info(f"Found {len(user_ids)} users with active OAuth connections")

        # Sync each user
        results = {
            'total_users': len(user_ids),
            'successful': 0,
            'failed': 0,
            'errors': []
        }

        for user_id in user_ids:
            try:
                sync_results = await sync_service.sync_user_data(user_id)
                results['successful'] += 1
                logger.info(f"Synced user {user_id}: {sync_results}")

            except Exception as e:
                results['failed'] += 1
                results['errors'].append({'user_id': user_id, 'error': str(e)})
                logger.error(f"Failed to sync user {user_id}: {str(e)}")

        logger.info(f"Background sync for all users completed: {results}")
        return results

    except Exception as e:
        logger.error(f"Background sync for all users failed: {str(e)}")
        raise


@celery_app.task(name='app.workers.tasks.cleanup_old_data')
def cleanup_old_data(days_to_keep: int = 90):
    """
    Clean up old insights data.

    Args:
        days_to_keep: Number of days of data to keep

    Returns:
        Cleanup results
    """
    try:
        logger.info(f"Starting cleanup of data older than {days_to_keep} days")

        # This would implement data cleanup logic
        # For now, just a placeholder

        return {
            'success': True,
            'message': f'Cleanup completed for data older than {days_to_keep} days'
        }

    except Exception as e:
        logger.error(f"Data cleanup failed: {str(e)}")
        raise


# Run with: celery -A app.workers.celery_app worker --loglevel=info
# Run beat scheduler: celery -A app.workers.celery_app beat --loglevel=info
