from __future__ import print_function
import os

from cachecontrol import CacheControl
from cachecontrol.caches.file_cache import FileCache
import click as cli
import requests

from .cache import SCOCAHeuristic
from .constants import DOCKET_LIST_ENDPOINT, DOCKET_LIST_FILTERS
from .http import filters_to_url_params, get_requests_header, get_response_json
from .models import CaseFiling


def get_active_docket(http_session, filters=DOCKET_LIST_FILTERS):
    filtered_endpoint = DOCKET_LIST_ENDPOINT + filters_to_url_params(filters)
    response = http_session.get(filtered_endpoint)
    active_docket = []

    while True:
        response_json = get_response_json(response)

        for docket_entry in response_json['results']:
            new_case_filing = CaseFiling(docket_entry)
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
    CaseFiling.set_http_session(http_session)

    active_docket = get_active_docket(http_session)
    print(active_docket)

    http_session.close()


main()
