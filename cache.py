from calendar import timegm
from datetime import datetime
from email.utils import formatdate, parsedate

from cachecontrol.heuristics import BaseHeuristic

from .date import local_to_utc, next_posting_date


class SCOCAHeuristic(BaseHeuristic):
    def update_headers(self, response):
        date = parsedate(response.headers['date'])
        expires_local = next_posting_date(datetime(*date[:6]))
        expires_utc = local_to_utc(expires_local)
        return {
            'expires': formatdate(timegm(expires_utc.timetuple())),
            'cache-control': 'public',
        }

    def warning(self, response):
        return '110 - "automatically cached, response is stale"'