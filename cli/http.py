from calendar import timegm
from datetime import datetime
from email.utils import formatdate, parsedate
import os
import urllib

from cachecontrol import CacheControl
from cachecontrol.caches.file_cache import FileCache
from cachecontrol.heuristics import BaseHeuristic
import requests

import date
import utils


COURTLISTENER_BASE_URL = 'https://www.courtlistener.com'
COURTLISTENER_REST_API = COURTLISTENER_BASE_URL + '/api/rest/v3'

DOCKET_LIST_ENDPOINT = COURTLISTENER_REST_API + '/dockets/'
DOCKET_LIST_FILTERS = {
    'court': 'cal',
    'clusters__date_filed__gte': date.DEFAULT_START_DATE,
    'order_by': ['-date_modified', '-date_created'],
}
OPINION_CLUSTER_ENDPOINT = COURTLISTENER_REST_API + '/clusters/{}/'  # {} is ID
OPINION_CLUSTER_FILTERS = {
    # As of 25-Jun-2019, the CourtListener API implementation always
    # sets the following fields as such, but would be useful for our
    # purposes if the implementation changes in the future:
    # - panel, non_participating_judges, judges: empty/null
    'fields': ['id', 'absolute_url', 'panel', 'non_participating_judges',
               'sub_opinions', 'judges', 'date_filed',
               'date_filed_is_approximate']
}
OPINION_INSTANCE_ENDPOINT = COURTLISTENER_REST_API + '/opinions/{}/'  # {} is ID
OPINION_INSTANCE_FILTERS = {
    # As of 25-Jun-2019, the CourtListener API implementation always
    # sets the following fields as such, but would be useful for our
    # purposes if the implementation changes in the future:
    # - author, joined_by, author_str: empty/null
    # - type: '010combined'
    'fields': ['id', 'author', 'joined_by', 'author_str', 'type', 'sha1',
               'download_url', 'plain_text'],
}

DEFAULT_REQUESTS_HEADER = {'Accept': 'application/json'}


class CacheHeuristic(BaseHeuristic):
    def update_headers(self, response):
        response_date = parsedate(response.headers['date'])
        expires_local = date.next_posting_date(datetime(*response_date[:6]))
        expires_utc = date.local_to_utc(expires_local)
        return {
            'expires': formatdate(timegm(expires_utc.timetuple())),
            'cache-control': 'public',
        }

    def warning(self, response):
        return '110 - "automatically cached, response is stale"'


def filters_to_url_params(filter_dict, begin='?'):
    """Takes a dictionary of filters to put in the form of encoded URL
    parameters, beginning with BEGIN. Parameter keys are strings and
    parameter values are either strings or lists of strings. Parameter
    values that are lists of strings are joined by commas.
    """
    params = []
    for k, v in filter_dict.items():
        # URL encode the key except for the last char if it's an
        # exclamation mark. See:
        # https://www.courtlistener.com/api/rest-info/?#field-selection
        if k[-1] == '!':
            k_quote = urllib.quote(k[:-1]) + '!'
        else:
            k_quote = urllib.quote(k)
        # URL encode the value. If a list, encoded elements will be
        # joined with commas. See:
        # https://www.courtlistener.com/api/rest-info/?#field-selection
        if isinstance(v, list):
            v_quote = ','.join(map(urllib.quote, v))
        else:
            v_quote = urllib.quote(v)
        param_str = '{}={}'.format(k_quote, v_quote)
        params.append(param_str)
    return begin + '&'.join(params)


def get_requests_header():
    header = DEFAULT_REQUESTS_HEADER.copy()
    token_filepath = utils.project_path('config', 'courtlistener_api.token')
    with open(token_filepath, 'r', 1) as token_file:
        token = token_file.read().strip()
        header['Authorization'] = 'Token {}'.format(token)
    return header


def get_response_json(response):
    try:
        response.raise_for_status()  # HTTPError
        return response.json()  # ValueError
    except requests.HTTPError as e:
        if response.status_code == 429:
            utils.error(e, 'API request quota reached. Is the CourtListener API token set?')
        else:
            raise NotImplementedError(e)  # TODO
    except ValueError as e:
        raise NotImplementedError(e)  # TODO


def start_http_session():
    # Start the cached HTTP Session.
    # Cache directory will be created if it doesn't exist.
    cache_path = utils.project_path('.cache')
    http_session = CacheControl(requests.Session(),
                                heuristic=CacheHeuristic(),
                                cache=FileCache(cache_path))
    http_session.headers = get_requests_header()
    return http_session
