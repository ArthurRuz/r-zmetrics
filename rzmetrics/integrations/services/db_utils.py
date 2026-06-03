import logging
import threading
import time
from functools import wraps

from django.db import OperationalError, close_old_connections


logger = logging.getLogger(__name__)

LIVE_DB_WRITE_LOCK = threading.Lock()

DB_LOCKED_MAX_RETRIES = 3
DB_LOCKED_RETRY_DELAY_SEC = 0.5


def retry_on_db_locked(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        for attempt in range(DB_LOCKED_MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except OperationalError as exc:
                is_locked = 'locked' in str(exc).lower()
                is_last_attempt = attempt >= DB_LOCKED_MAX_RETRIES - 1

                if not is_locked or is_last_attempt:
                    raise

                delay = DB_LOCKED_RETRY_DELAY_SEC * (attempt + 1)
                logger.warning(
                    'База заблокирована, повтор через %.1f с (попытка %s/%s)',
                    delay,
                    attempt + 2,
                    DB_LOCKED_MAX_RETRIES,
                )
                time.sleep(delay)

    return wrapper


def with_scheduler_db_connection(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        close_old_connections()
        try:
            return func(*args, **kwargs)
        finally:
            close_old_connections()

    return wrapper
