import os.path
import sqlite3

from .utils import project_path, print_err


_DB_PATH = project_path('.db')


def exists():
    return os.path.isfile(_DB_PATH)


def init():
    init_sql_path = project_path('init.sql')
    db_connection = connect()
    try:
        try:
            with db_connection, open(init_sql_path) as init_sql_file:
                init_sql = init_sql_file.read()
                db_connection.executescript(init_sql)
        except Exception:
            print_err('Could not initialize database')
            raise
    finally:
        db_connection.close()


def connect(isolation_level=None):
    return sqlite3.connect(_DB_PATH, isolation_level=isolation_level)


# Initialize the database if it doesn't exist when this module is imported.
if not exists():
    init()
