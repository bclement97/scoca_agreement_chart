import os
import re
import urllib
import warnings

from requests import HTTPError

from constants import DATE_FORMAT, DEFAULT_REQUESTS_HEADER
import regex


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


def date_to_str(date):
    return date.strftime(DATE_FORMAT)


def get_docket_number(text):
    docket_nums = re.findall(regex.DOCKET_NUM, text)
    if len(docket_nums) == 0:
        raise RuntimeError('No docket number found.')
    elif len(set(docket_nums)) > 1:
        raise RuntimeError('Multiple docket numbers found.')
    return docket_nums[0]


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
