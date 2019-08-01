import requests

from .constants import COURTLISTENER_BASE_URL, OPINION_CLUSTER_FILTERS
from .http import filters_to_url_params, get_response_json


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
        abs_url = self._opinion_cluster.get('absolute_url')
        return COURTLISTENER_BASE_URL + abs_url if abs_url else None

    @property
    def published_on(self):
        return self._opinion_cluster.get('date_filed')

    @staticmethod
    def set_http_session(http_session):
        CaseFiling._http_session = http_session

    def __get_opinion_cluster(self):
        clusters = self._docket_entry.get('clusters')
        if not isinstance(clusters, list) or len(clusters) != 1:
            raise ValueError  # TODO (custom unexpected value error?)
        filtered_endpoint = clusters[0] + filters_to_url_params(OPINION_CLUSTER_FILTERS)
        response = CaseFiling._http_session.get(filtered_endpoint)
        return get_response_json(response)

    def __str__(self):
        return self.docket_number
