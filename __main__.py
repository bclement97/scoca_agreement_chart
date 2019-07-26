from __future__ import print_function

import cachecontrol
import click as cli
import requests

from .constants import DOCKET_LIST_ENDPOINT, DOCKET_LIST_FILTERS
from .utils import filters_to_url_params, get_requests_header


class CaseFiling(object):
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

    def __get_opinion_cluster(self):
        if len(self._docket_entry['clusters']) != 1:
            raise NotImplementedError  # TODO (custom unexpected value error?)
        raise NotImplementedError

    def __str__(self):
        return self.docket_number


def get_active_docket(http_session, filters=DOCKET_LIST_FILTERS):
    filtered_endpoint = DOCKET_LIST_ENDPOINT + filters_to_url_params(filters)
    response = http_session.get(filtered_endpoint)
    active_docket = []

    while True:
        try:
            response.raise_for_status()  # HTTPError
            response_json = response.json()  # ValueError
        except requests.HTTPError:
            raise NotImplementedError  # TODO
        except ValueError:
            raise NotImplementedError  # TODO

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

    active_docket = get_active_docket(http_session)
    print(repr(active_docket[0]))

    http_session.close()


main()
