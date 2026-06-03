import logging

from django.db.backends.signals import connection_created


logger = logging.getLogger(__name__)


def _enable_sqlite_wal(sender, connection, **kwargs):
    if connection.vendor != 'sqlite':
        return

    with connection.cursor() as cursor:
        cursor.execute('PRAGMA journal_mode=WAL;')


connection_created.connect(_enable_sqlite_wal)
