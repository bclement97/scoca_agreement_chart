import csv
import os.path
import sqlite3

from .models import OpinionType
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


# def start(isolation_level=None):
#     # Start the DB Connection.
#     db_exists = os.path.isfile(_db_path)
#     # Creates db file if doesn't exist.
#     db_conn = sqlite3.connect(_db_path, isolation_level=isolation_level)
#     # Initialize the DB if needed.
#     if not db_exists:
#         init(db_conn)
#         populate_justices_table(db_conn)
#         populate_opinion_types_table(db_conn)
#     return db_conn


def populate_justices_table(db_conn):
    justices_path = project_path('config', 'justices.csv')
    justices_sql = """
        INSERT INTO justices (
            fullname,
            short_name,
            shorthand
        )
        VALUES (?, ?, ?); 
    """
    try:
        with db_conn, open(justices_path) as justices_csv:
            justices_reader = csv.DictReader(justices_csv)
            for justice in justices_reader:
                db_conn.execute(justices_sql, (
                    # Sqlite3 requires unicode.
                    justice['fullname'].decode('utf-8'),
                    justice['short_name'].decode('utf-8'),
                    justice['shorthand'].decode('utf-8')
                ))
    except Exception:
        print_err('Could not populate table `justices`')
        raise


def populate_opinion_types_table(db_conn):
    opinion_types_sql = 'INSERT INTO opinion_types (type) VALUES (?);'
    try:
        with db_conn:
            for opinion_type in list(OpinionType):
                db_conn.execute(opinion_types_sql, (str(opinion_type),))
    except Exception:
        print_err('Could not populate table `opinion_types`')
        raise


# Initialize the database if it doesn't exist when this module is imported.
if not exists():
    init()
