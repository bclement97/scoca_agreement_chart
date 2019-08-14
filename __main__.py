from __future__ import print_function
import os
import sqlite3

from cachecontrol import CacheControl
from cachecontrol.caches.file_cache import FileCache
import click as cli
import requests

from .cache import SCOCAHeuristic
from .http import (
    DOCKET_LIST_ENDPOINT, DOCKET_LIST_FILTERS,
    filters_to_url_params, get_requests_header, get_response_json
)
from .models import CaseFiling


def get_active_docket(http_session, filters=DOCKET_LIST_FILTERS):
    filtered_endpoint = DOCKET_LIST_ENDPOINT + filters_to_url_params(filters)
    response = http_session.get(filtered_endpoint)
    active_docket = []

    while True:
        response_json = get_response_json(response)

        for docket_entry in response_json['results']:
            new_case_filing = CaseFiling(docket_entry, http_session)
            active_docket.append(new_case_filing)

        if response_json['next'] is None:
            break
        response = http_session.get(response_json['next'])

    return active_docket


def main():
    dir_path = os.path.dirname(os.path.realpath(__file__))

    cache_path = os.path.join(dir_path, '.cache')
    http_session = CacheControl(requests.Session(), heuristic=SCOCAHeuristic(), cache=FileCache(cache_path))
    http_session.headers = get_requests_header()

    db_path = os.path.join(dir_path, 'scoca.db')
    conn = sqlite3.connect(db_path)
    if not conn:
        msg = 'Could not connect to database: {}'.format(db_path)
        http_session.close()
        raise RuntimeError(msg)

    active_docket = get_active_docket(http_session)
    for case_filing in active_docket:
        # Ignores case filings whose docket numbers already exist in the table
        try:
            with conn:
                conn.execute(
                    'INSERT INTO case_filings (docket_number, url, plain_text, sha1, filed_on) VALUES (?, ?, ?, ?, ?)',
                    (
                        case_filing.docket_number,
                        case_filing.url,
                        case_filing.plain_text,
                        case_filing.sha1,
                        case_filing.filed_on
                    )
                )
        except sqlite3.IntegrityError:
            pass

    conn.close()
    http_session.close()


main()
