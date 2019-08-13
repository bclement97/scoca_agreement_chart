import requests

from .http import (
    COURTLISTENER_BASE_URL, OPINION_CLUSTER_FILTERS, OPINION_INSTANCE_FILTERS,
    filters_to_url_params, get_response_json
)


def _assert_unit_list(obj):
    if not isinstance(obj, list) or len(obj) != 1:
        raise ValueError  # TODO (custom unexpected value error?)


class CaseFiling(object):
    def __init__(self, docket_entry, http_session=requests):
        self._docket_entry = docket_entry
        self._http_session = http_session
        self._opinion_cluster = self.__get_opinion_cluster()
        self._opinion = self.__get_opinion()

    @property
    def docket_number(self):
        return self._docket_entry.get('docket_number')

    @property
    def url(self):
        abs_url = self._opinion_cluster.get('absolute_url')
        return COURTLISTENER_BASE_URL + abs_url if abs_url else None

    @property
    def plain_text(self):
        return self._opinion.get('plain_text')

    @property
    def sha1(self):
        return self._opinion.get('sha1')

    @property
    def published_on(self):
        return self._opinion_cluster.get('date_filed')

    def __get(self, endpoint, filter_dict):
        filtered_endpoint = endpoint + filters_to_url_params(filter_dict)
        response = self._http_session.get(filtered_endpoint)
        return get_response_json(response)

    def __get_opinion_cluster(self):
        clusters = self._docket_entry.get('clusters')
        _assert_unit_list(clusters)
        return self.__get(clusters[0], OPINION_CLUSTER_FILTERS)

    def __get_opinion(self):
        opinions = self._opinion_cluster.get('sub_opinions')
        _assert_unit_list(opinions)
        return self.__get(opinions[0], OPINION_INSTANCE_FILTERS)

    def __str__(self):
        return self.docket_number

    def __repr__(self):
        return '<CaseFiling: {}>'.format(self)
