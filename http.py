import os
import urllib
import warnings

from requests import HTTPError

from .constants import DEFAULT_REQUESTS_HEADER


def filters_to_url_params(filter_dict, begin='?'):
    """Takes a dictionary of filters to put in the form of encoded URL parameters, beginning with BEGIN.
    Parameter keys are strings and parameter values are either strings or lists of strings.
    Parameter values that are lists of strings are joined by commas.
    """
    params = []
    for k, v in filter_dict.items():
        # URL encode the key except for the last char if it's an exclamation mark. See:
        # https://www.courtlistener.com/api/rest-info/?#field-selection
        if k[-1] == '!':
            k_quote = urllib.quote(k[:-1]) + '!'
        else:
            k_quote = urllib.quote(k)
        # URL encode the value. If a list, encoded elements will be joined with commas. See:
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
    token = os.environ.get('COURTLISTENER_API_TOKEN')
    if token:
        header['Authorization'] = 'Token {}'.format(token)
    else:
        warnings.warn('No Court Listener API authorization token found.', RuntimeWarning)
    return header


def get_response_json(response):
    try:
        response.raise_for_status()  # HTTPError
        return response.json()  # ValueError
    except HTTPError:
        raise NotImplementedError  # TODO
    except ValueError:
        raise NotImplementedError  # TODO
