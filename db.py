import apsw
import os.path

import utils


_DB_PATH = utils.project_path('.db')


def exists():
    return os.path.isfile(_DB_PATH)


def init():
    utils.log('Initializing database')
    init_sql_path = utils.project_path('init.sql')
    db_connection = connect()
    try:
        with db_connection, open(init_sql_path) as init_sql_file:
            init_sql = init_sql_file.read()
            db_connection.cursor().execute(init_sql)
    finally:
        db_connection.close()


def connect():
    return apsw.Connection(_DB_PATH)


# Initialize the database if it doesn't exist when this module is imported.
if not exists():
    init()
