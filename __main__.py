from __future__ import print_function
import os.path
import sqlite3
import string

from cachecontrol import CacheControl
from cachecontrol.caches.file_cache import FileCache
import click as cli
import requests

from .cache import SCOCAHeuristic
from .http import (
    DOCKET_LIST_ENDPOINT, DOCKET_LIST_FILTERS,
    filters_to_url_params, get_requests_header, get_response_json
)
from .models import CaseFiling, Justice, MajorityOpinion, Opinion
import regex


def get_active_docket(http_session, filters=DOCKET_LIST_FILTERS):
    active_docket = []
    next_page = DOCKET_LIST_ENDPOINT + filters_to_url_params(filters)
    while True:
        response = get_response_json(http_session.get(next_page))
        for docket_entry in response['results']:
            new_case_filing = CaseFiling(docket_entry, http_session)
            active_docket += [new_case_filing]
        next_page = response.get('next')
        if not next_page:
            return active_docket


def save_active_docket(db_connection, active_docket):
    """Inserts CaseFilings from ACTIVE_DOCKET into DB_CONNECTION,
    ignoring ones that already exist in the table.

    :param db_connection: The database connection
    :param active_docket: An iterable of CaseFilings
    :return: First return value is a list of inserted CaseFilings.
    Second return value is a list of ignored CaseFilings.
    """

    sql = """
        INSERT INTO case_filings (
            docket_number,
            url,
            plain_text,
            sha1,
            filed_on
        )
        VALUES (?, ?, ?, ?, ?);
    """

    inserted, ignored = [], []
    for case_filing in active_docket:
        try:
            # Automatically commit on success.
            with db_connection:
                db_connection.execute(sql, (case_filing.docket_number,
                                            case_filing.url,
                                            case_filing.plain_text,
                                            case_filing.sha1,
                                            case_filing.filed_on))
        except sqlite3.IntegrityError:
            # Ignore case filings whose docket numbers already exist in
            # the table.
            ignored += [case_filing]
        else:
            inserted += [case_filing]

    return inserted, ignored


def get_opinions(case_filing):
    opinion_tuples = regex.findall_opinions(case_filing.plain_text)
    if not len(opinion_tuples):
        return []
    majority_tuple, secondary_tuples = opinion_tuples[0], opinion_tuples[1:]
    majority_opinion = MajorityOpinion(case_filing, *majority_tuple[:3])
    secondary_opinions = [Opinion(case_filing, *tup[3:])
                          for tup in secondary_tuples]
    # return secondary_opinions + [majority_opinion]
    return [majority_opinion] + secondary_opinions


def save_opinions(db_connection, opinions):
    insert_opinion_sql = """
        INSERT INTO opinions (
            case_filing_docket_number,
            opinion_type_id,
            authoring_justice_id
        )
        VALUES (?, ?, ?);
    """
    opinion_id_sql = """
        SELECT id FROM opinions
        WHERE case_filing_docket_number = ?
            AND opinion_type_id = ?
            AND authoring_justice_id = ?
    """
    concurrence_sql = """
        INSERT INTO concurrences (
            opinion_id,
            justice_id
        )
        VALUES (?, ?)
    """

    # FIXME: This logic looks digusting. Does it even work?

    inserted, ignored, partial = [], [], []
    for opinion in opinions:
        try:
            justices = Justice.get_all_by_name(db_connection)
            authoring_justice_id = justices[opinion.authoring_justice].id
            # Automatically commit on success.
            with db_connection:
                db_connection.execute(insert_opinion_sql, (
                    opinion.case_filing.docket_number,
                    opinion.type.value,
                    authoring_justice_id
                ))
            # Get the ID of the inserted opinion.
            cur = db_connection.execute(opinion_id_sql, (
                opinion.case_filing.docket_number,
                opinion.type.value,
                authoring_justice_id
            ))
            (opinion_id,) = cur.fetchone()
            # Insert a concurrence row for each concurring justice.
            for concurring_justice in opinion.concurring_justices:
                try:
                    concurring_justice_id = justices[concurring_justice].id
                    with db_connection:
                        db_connection.execute(concurrence_sql, (
                            opinion_id,
                            concurring_justice_id
                        ))
                except sqlite3.IntegrityError:
                    partial += [opinion]
        except sqlite3.IntegrityError:
            ignored += [opinion]
        else:
            if opinion not in partial:
                inserted += [opinion]

    return inserted, ignored, partial


def main():
    dir_path = os.path.dirname(os.path.realpath(__file__))

    # Start the cached HTTP Session.
    # Cache directory will be created if it doesn't exist.
    cache_path = os.path.join(dir_path, '.cache')
    http_session = CacheControl(requests.Session(), heuristic=SCOCAHeuristic(),
                                cache=FileCache(cache_path))
    http_session.headers = get_requests_header()
    try:
        # Start the DB Connection.
        db_path = os.path.join(dir_path, '.db')
        if not os.path.isfile(db_path):
            msg = 'Database does not exist: {}'.format(db_path)
            raise RuntimeError(msg)
        db_conn = sqlite3.connect(db_path)
        try:
            # Start main logic requiring the HTTP Session and DB
            # Connection.
            active_docket = get_active_docket(http_session)
            # CaseFilings whose docket numbers end in a letter. Only 'A'
            # and 'M' are known to occur, but others should be flagged
            # regardless.
            flagged_case_filings = set([cf for cf in active_docket
                                        if cf.docket_number[-1]
                                        in string.ascii_letters])
            _, _ = save_active_docket(db_conn, active_docket)
            for case_filing in active_docket:
                opinions = get_opinions(case_filing)
                if not len(opinions):
                    flagged_case_filings.add(case_filing)
                    continue
                _, _, _ = save_opinions(db_conn, opinions)
        finally:
            db_conn.close()
    finally:
        http_session.close()


main()
