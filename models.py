from enum import Enum, unique

import requests

from .http import (
    COURTLISTENER_BASE_URL, OPINION_CLUSTER_FILTERS, OPINION_INSTANCE_FILTERS,
    filters_to_url_params, get_response_json
)
import regex


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
    def filed_on(self):
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
        return '<CaseFiling: {}>'.format(self.docket_number)


@unique
class OpinionType(Enum):
    MAJORITY = 1
    CONCURRING = 2
    DISSENTING = 3
    CONCURRING_AND_DISSENTING = 4

    def __str__(self):
        return self.name.lower().replace('_', ' ')

    @staticmethod
    def to_type(val):
        if isinstance(val, (str, unicode)):
            return OpinionType[val.upper().replace(' ', '_')]
        elif isinstance(val, int):
            return OpinionType[val]
        raise NotImplementedError


class Opinion(object):
    def __init__(self, case_filing, authoring_justice, _type, concurring_chief, concurring_assocs):
        self.case_filing = case_filing
        self.authoring_justice = authoring_justice
        self.type = _type if isinstance(_type, OpinionType) else OpinionType.to_type(_type)
        self.concurring_justices = [concurring_chief] if concurring_chief else []
        self.concurring_justices += regex.split_justices(concurring_assocs)

    @property
    def utf8_authoring_justice(self):
        return self.authoring_justice.encode('utf-8')

    @property
    def utf8_concurring_justices(self):
        return [justice.encode('utf-8') for justice in self.concurring_justices]

    def __str__(self):
        return '[{}] {} ({}): {}'.format(self.case_filing.docket_number, self.utf8_authoring_justice,
                                         str(self.type).upper(), ', '.join(self.utf8_concurring_justices))

    def __repr__(self):
        return '<Opinion [{}]: {} ({})>'.format(self.case_filing.docket_number, self.utf8_authoring_justice,
                                                str(self.type).upper())


class MajorityOpinion(Opinion):
    def __init__(self, case_filing, authoring_justice, concurring_chief, concurring_assocs):
        super(MajorityOpinion, self).__init__(case_filing, authoring_justice, OpinionType.MAJORITY, concurring_chief,
                                              concurring_assocs)
