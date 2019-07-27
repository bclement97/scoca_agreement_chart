from __future__ import print_function

import cachecontrol
import click as cli
import requests

from .constants import DOCKET_LIST_ENDPOINT, DOCKET_LIST_FILTERS, OPINION_CLUSTER_ENDPOINT, OPINION_CLUSTER_FILTERS
from .utils import filters_to_url_params, get_requests_header, get_response_json


class CaseFiling(object):
    # Default to no HTTP Session
    _http_session = requests

    def __init__(self, docket_entry):
        self._docket_entry = docket_entry
        self._opinion_cluster = self.__get_opinion_cluster()

    @property
    def docket_number(self):
        return self._docket_entry.get('docket_number')

    @property
    def url(self):
        raise NotImplementedError

    @property
    def published_on(self):
        raise NotImplementedError

    @staticmethod
    def set_http_session(http_session):
        CaseFiling._http_session = http_session

    def __get_opinion_cluster(self):
        if len(self._docket_entry['clusters']) != 1:
            raise ValueError  # TODO (custom unexpected value error?)

        filtered_endpoint = self._docket_entry['clusters'][0] + filters_to_url_params(OPINION_CLUSTER_FILTERS)
        response = CaseFiling._http_session.get(filtered_endpoint)
        return get_response_json(response)

    def __str__(self):
        return self.docket_number


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
    http_session = requests.Session()
    http_session.headers = get_requests_header()
    CaseFiling.set_http_session(http_session)

    active_docket = get_active_docket(http_session)
    print(active_docket)

    http_session.close()


main()
