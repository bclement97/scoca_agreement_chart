import csv
import os.path
import sqlite3

from .models import OpinionType
from .utils import project_path, print_err


def start_db():
    # Start the DB Connection.
    db_path = project_path('.db')
    db_exists = os.path.isfile(db_path)
    # Creates db file if doesn't exist.
    db_conn = sqlite3.connect(db_path)
    # Initialize the DB if needed.
    if not db_exists:
        init_db(db_conn)
        populate_justices_table(db_conn)
        populate_opinion_types_table(db_conn)
    return db_conn


def init_db(db_conn):
    init_sql_path = project_path('init.sql')
    try:
        with db_conn, open(init_sql_path) as init_sql_file:
            init_sql = init_sql_file.read()
            db_conn.executescript(init_sql)
    except Exception:
        print_err('Could not initialize database')
        raise


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
