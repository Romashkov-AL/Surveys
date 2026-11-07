from django.db import connection


def ping_database() -> None:
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
        cursor.fetchone()
